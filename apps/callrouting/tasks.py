import logging

from celery import shared_task
from django.conf import settings
from django.db import DatabaseError, InterfaceError, OperationalError, transaction
from django.utils import timezone

from apps.calllogs.models import CallLog
from apps.callrouting.models import RoutingEvent, RoutingWhatsAppMessage
from apps.callrouting.provider import DoubleTickPermanentError, DoubleTickTemplateProvider, DoubleTickTransientError, digits_only
from apps.callrouting.services import RoutingService
from apps.callrouting.whatsapp import RoutingWhatsAppService
from apps.doubletick.models import DoubleTickChannel, DoubleTickConversation, DoubleTickCustomer, DoubleTickMessage

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(OperationalError, InterfaceError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def process_call_log_routing(self, call_log_id):
    """Process routing for one CallLog ID. Safe to retry."""
    try:
        call_log = CallLog.objects.select_related("branch", "device", "contact").get(id=call_log_id)
    except CallLog.DoesNotExist:
        logger.warning("Routing task skipped: CallLog not found", extra={"call_log_id": str(call_log_id)})
        return {"status": "missing", "call_log_id": str(call_log_id)}

    logger.info(
        "Routing task started",
        extra={
            "call_log_id": str(call_log.id),
            "branch_id": str(call_log.branch_id) if call_log.branch_id else "",
            "task_retries": self.request.retries,
        },
    )
    try:
        routing_request = RoutingService.process_call_log(call_log)
        RoutingWhatsAppService.prepare_for_request(routing_request)
    except DatabaseError:
        raise
    except Exception:
        logger.exception(
            "Routing task failed",
            extra={
                "call_log_id": str(call_log.id),
                "branch_id": str(call_log.branch_id) if call_log.branch_id else "",
                "task_retries": self.request.retries,
            },
        )
        raise

    logger.info(
        "Routing task completed",
        extra={
            "call_log_id": str(call_log.id),
            "routing_request_id": str(routing_request.id),
            "routing_status": routing_request.status,
        },
    )
    return {
        "status": routing_request.status,
        "routing_request_id": str(routing_request.id),
        "call_log_id": str(call_log.id),
    }


def _waba_sender():
    return getattr(settings, "DOUBLETICK_SEND_FROM_WABA_NUMBER", "")


def _provider_conversation(message, from_waba):
    routing_request = message.routing_request
    customer_name = (message.template_payload or {}).get("customer_name") or "Customer"
    normalized_phone = routing_request.normalized_phone or message.recipient_phone
    channel = DoubleTickChannel.objects.filter(waba_number=digits_only(from_waba)).first()
    customer = DoubleTickCustomer.objects.filter(normalized_phone=normalized_phone).first()
    if not customer:
        customer = DoubleTickCustomer.objects.create(
            phone_number=message.recipient_phone,
            normalized_phone=normalized_phone,
            customer_name=customer_name,
            channel=channel,
        )
    conversation = (
        DoubleTickConversation.objects.filter(customer=customer, channel=channel).order_by("-last_message_at", "-created_at").first()
        or DoubleTickConversation.objects.create(customer=customer, channel=channel)
    )
    return customer, conversation


@shared_task(bind=True, max_retries=3)
def send_routing_whatsapp_message(self, routing_whatsapp_message_id):
    """Send one queued CallRouting WhatsApp template through DoubleTick."""
    with transaction.atomic():
        message = (
            RoutingWhatsAppMessage.objects.select_for_update()
            .select_related("routing_request")
            .get(id=routing_whatsapp_message_id)
        )
        if message.status in [
            RoutingWhatsAppMessage.Status.SENT,
            RoutingWhatsAppMessage.Status.DELIVERED,
            RoutingWhatsAppMessage.Status.READ,
        ] or message.provider_message_id:
            return {"status": "already_sent", "message_id": str(message.id)}
        if message.routing_request.status != "routed":
            message.status = RoutingWhatsAppMessage.Status.FAILED
            message.failure_reason = "ROUTING_REQUEST_NOT_ROUTED"
            message.save(update_fields=["status", "failure_reason", "updated_at"])
            return {"status": "failed", "reason": message.failure_reason}
        message.status = RoutingWhatsAppMessage.Status.SENDING
        message.save(update_fields=["status", "updated_at"])

    from_waba = _waba_sender()
    variables = (message.template_payload or {}).get("template_variables") or []
    try:
        result = DoubleTickTemplateProvider.send(message.recipient_phone, from_waba, variables)
    except DoubleTickTransientError as exc:
        with transaction.atomic():
            locked = RoutingWhatsAppMessage.objects.select_for_update().get(id=routing_whatsapp_message_id)
            locked.failure_reason = str(exc)
            locked.provider_payload = exc.provider_payload
            if self.request.retries >= self.max_retries:
                locked.status = RoutingWhatsAppMessage.Status.FAILED
                locked.failed_at = timezone.now()
                locked.save(update_fields=["status", "failed_at", "failure_reason", "provider_payload", "updated_at"])
                RoutingEvent.objects.create(
                    routing_request=locked.routing_request,
                    event_type=RoutingEvent.EventType.WHATSAPP_FAILED,
                    message=str(exc),
                    metadata={"message_id": str(locked.id), "retryable": True},
                )
                return {"status": "failed", "reason": str(exc)}
            locked.status = RoutingWhatsAppMessage.Status.QUEUED
            locked.save(update_fields=["status", "failure_reason", "provider_payload", "updated_at"])
        raise self.retry(exc=exc, countdown=2**self.request.retries)
    except DoubleTickPermanentError as exc:
        with transaction.atomic():
            locked = RoutingWhatsAppMessage.objects.select_for_update().get(id=routing_whatsapp_message_id)
            locked.status = RoutingWhatsAppMessage.Status.FAILED
            locked.failed_at = timezone.now()
            locked.failure_reason = str(exc)
            locked.provider_payload = exc.provider_payload
            locked.save(update_fields=["status", "failed_at", "failure_reason", "provider_payload", "updated_at"])
            RoutingEvent.objects.create(
                routing_request=locked.routing_request,
                event_type=RoutingEvent.EventType.WHATSAPP_FAILED,
                message=str(exc),
                metadata={"message_id": str(locked.id), "retryable": False},
            )
        return {"status": "failed", "reason": str(exc)}

    with transaction.atomic():
        locked = (
            RoutingWhatsAppMessage.objects.select_for_update()
            .select_related("routing_request")
            .get(id=routing_whatsapp_message_id)
        )
        if locked.provider_message_id:
            return {"status": "already_sent", "message_id": str(locked.id)}
        customer, conversation = _provider_conversation(locked, from_waba)
        now = timezone.now()
        doubletick_message = DoubleTickMessage.objects.create(
            conversation=conversation,
            customer=customer,
            message_id=result["message_id"],
            dt_message_id=result["message_id"],
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin=DoubleTickMessage.Origin.API,
            message_type="template",
            text=locked.template_name,
            status=DoubleTickMessage.Status.SENT,
            customer_number=locked.recipient_phone,
            waba_number=from_waba,
            message_timestamp=now,
            sent_at=now,
            raw_payload=result["provider_payload"],
        )
        locked.doubletick_message = doubletick_message
        locked.provider_message_id = result["message_id"]
        locked.status = RoutingWhatsAppMessage.Status.SENT
        locked.sent_at = now
        locked.failure_reason = ""
        locked.provider_payload = result["provider_payload"]
        locked.save(update_fields=[
            "doubletick_message",
            "provider_message_id",
            "status",
            "sent_at",
            "failure_reason",
            "provider_payload",
            "updated_at",
        ])
        RoutingEvent.objects.create(
            routing_request=locked.routing_request,
            event_type=RoutingEvent.EventType.WHATSAPP_SENT,
            metadata={"message_id": str(locked.id), "provider_message_id": locked.provider_message_id},
        )
        return {"status": "sent", "provider_message_id": locked.provider_message_id}

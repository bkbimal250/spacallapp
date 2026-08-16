import logging
import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.branches.services import BranchOperatingHoursService
from apps.callrouting.models import RoutingEvent, RoutingRequest, RoutingWhatsAppMessage
from apps.callrouting.provider import DoubleTickTemplateProvider
from apps.callrouting.services import PhoneNormalizationService

logger = logging.getLogger(__name__)


ACTIVE_WHATSAPP_STATUSES = {
    RoutingWhatsAppMessage.Status.QUEUED,
    RoutingWhatsAppMessage.Status.SENDING,
    RoutingWhatsAppMessage.Status.SENT,
    RoutingWhatsAppMessage.Status.DELIVERED,
    RoutingWhatsAppMessage.Status.READ,
}


class RoutingWhatsAppErrorCode:
    INVALID_RECIPIENT = "INVALID_RECIPIENT"
    NO_SELECTED_CANDIDATES = "NO_SELECTED_CANDIDATES"
    TEMPLATE_NOT_CONFIGURED = "TEMPLATE_NOT_CONFIGURED"
    PROVIDER_TEMPLATE_API_NOT_CONFIGURED = "PROVIDER_TEMPLATE_API_NOT_CONFIGURED"
    CALL_ROUTING_WHATSAPP_DISABLED = "CALL_ROUTING_WHATSAPP_DISABLED"
    DUPLICATE_RECIPIENT_24H = "DUPLICATE_RECIPIENT_24H"


def mask_phone(phone):
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) <= 4:
        return "****"
    return f"****{digits[-4:]}"


@dataclass(frozen=True)
class BranchRecommendation:
    spa_name: str
    location: str
    open_until: str
    phone: str
    details_url: str


class RoutingTemplateDataBuilder:
    """Build business template data from persisted routing decisions."""

    @staticmethod
    def _location(branch):
        city = branch.location_city.name if branch.location_city_id else branch.city
        area = branch.location_area.name if branch.location_area_id else branch.area
        return ", ".join(part for part in [area, city] if part)

    @staticmethod
    def _open_until(branch, at_datetime):
        hours = BranchOperatingHoursService.get_applicable_hours(branch, at_datetime)
        if hours and hours.is_24_hours:
            return "24 by 7 open hr"
        if not hours or hours.is_closed or not hours.closes_at:
            return ""
        return hours.closes_at.strftime("%I:%M %p").lstrip("0")

    @classmethod
    def _recommendation(cls, candidate, at_datetime):
        branch = candidate.branch
        return BranchRecommendation(
            spa_name=branch.spa_name,
            location=cls._location(branch),
            open_until=cls._open_until(branch, at_datetime),
            phone=branch.phone or "",
            details_url=branch.shared_link or "",
        )

    @staticmethod
    def format_recommendations(recommendations):
        def bold(value):
            return f"*{value}*" if value else ""

        blocks = []
        for recommendation in recommendations:
            lines = [bold(recommendation.get("spa_name", ""))]
            if recommendation.get("location"):
                lines.append(f"Location: {bold(recommendation['location'])}")
            if recommendation.get("open_until"):
                label = "Open Status" if recommendation["open_until"] == "24 by 7 open hr" else "Open Until"
                lines.append(f"{label}: {bold(recommendation['open_until'])}")
            if recommendation.get("phone"):
                lines.append(f"Phone: {bold(recommendation['phone'])}")
            if recommendation.get("details_url"):
                lines.append(f"Map Link: {bold(recommendation['details_url'])}")
            blocks.append("\n".join(line for line in lines if line))
        return "\n\n".join(block for block in blocks if block)

    @classmethod
    def build(cls, routing_request):
        call_log = routing_request.call_log
        source_branch = call_log.branch
        contact = routing_request.contact or call_log.contact
        selected = list(
            routing_request.candidates.filter(is_selected=True, is_eligible=True)
            .select_related("branch", "branch__location_city", "branch__location_area")
            .order_by("rank", "-relevance_score", "branch__code", "branch__spa_name")
        )
        selected_24_hours = []
        for candidate in selected:
            hours = BranchOperatingHoursService.get_applicable_hours(
                candidate.branch,
                routing_request.call_time or call_log.call_time,
            )
            if hours and hours.is_24_hours:
                selected_24_hours.append(candidate)
        selected = selected_24_hours
        recommendations = [
            cls._recommendation(candidate, routing_request.call_time or call_log.call_time).__dict__
            for candidate in selected
        ]
        source_location = cls._location(source_branch) if source_branch else ""
        enquiry_time = timezone.localtime(routing_request.call_time or call_log.call_time).strftime("%Y-%m-%d %I:%M %p")
        customer_name = getattr(contact, "name", "") or "Customer"
        source_spa_name = source_branch.spa_name if source_branch else ""
        formatted_recommendations = cls.format_recommendations(recommendations)
        return {
            "customer_name": customer_name,
            "source_spa_name": source_spa_name,
            "source_spa_location": source_location,
            "enquiry_time": enquiry_time,
            "recommendations": recommendations,
            "formatted_recommendations": formatted_recommendations,
            "template_variables": [
                customer_name,
                source_spa_name,
                formatted_recommendations,
            ],
        }


class RoutingWhatsAppService:
    """Prepare routing WhatsApp records. Does not invent provider template APIs."""

    @staticmethod
    def _event(routing_request, event_type, message="", metadata=None):
        return RoutingEvent.objects.create(
            routing_request=routing_request,
            event_type=event_type,
            message=message,
            metadata=metadata or {},
        )

    @staticmethod
    def _idempotency_key(routing_request):
        return f"routing:{routing_request.id}:template:{routing_request.routing_rule_id or 'none'}"

    @staticmethod
    def _has_no_emoji(payload):
        encoded = str(payload).encode("ascii", errors="ignore").decode("ascii")
        return encoded == str(payload)

    @staticmethod
    def _recent_recipient_message(recipient, template_name, routing_request_id):
        cooldown_hours = max(0, int(getattr(settings, "CALL_ROUTING_WHATSAPP_RECIPIENT_COOLDOWN_HOURS", 24) or 0))
        if not recipient or not cooldown_hours:
            return None
        cutoff = timezone.now() - timedelta(hours=cooldown_hours)
        return (
            RoutingWhatsAppMessage.objects.filter(
                recipient_phone=recipient,
                template_name=template_name,
                status__in=ACTIVE_WHATSAPP_STATUSES,
                created_at__gte=cutoff,
            )
            .exclude(routing_request_id=routing_request_id)
            .order_by("-created_at")
            .first()
        )

    @classmethod
    def prepare_for_request(cls, routing_request):
        if routing_request.status != RoutingRequest.Status.ROUTED:
            return None

        routing_request = RoutingRequest.objects.select_related(
            "call_log",
            "call_log__branch",
            "call_log__branch__location_city",
            "call_log__branch__location_area",
            "call_log__contact",
            "routing_rule",
        ).get(id=routing_request.id)

        existing = routing_request.whatsapp_messages.filter(status__in=ACTIVE_WHATSAPP_STATUSES).first()
        if existing:
            return existing

        recipient = routing_request.normalized_phone or PhoneNormalizationService.normalize(routing_request.call_log.phone_number)
        template_name = routing_request.routing_rule.template_name if routing_request.routing_rule else ""
        template_language = routing_request.routing_rule.template_language if routing_request.routing_rule else "en"
        template_name = DoubleTickTemplateProvider.TEMPLATE_NAME
        template_language = DoubleTickTemplateProvider.LANGUAGE
        template_payload = RoutingTemplateDataBuilder.build(routing_request)
        idempotency_key = cls._idempotency_key(routing_request)

        status = RoutingWhatsAppMessage.Status.QUEUED
        queued_at = timezone.now()
        failure_reason = ""

        if not recipient:
            status = RoutingWhatsAppMessage.Status.FAILED
            queued_at = None
            failure_reason = RoutingWhatsAppErrorCode.INVALID_RECIPIENT
        elif not template_payload["recommendations"]:
            status = RoutingWhatsAppMessage.Status.CANCELLED
            queued_at = None
            failure_reason = RoutingWhatsAppErrorCode.NO_SELECTED_CANDIDATES
        elif not template_name:
            status = RoutingWhatsAppMessage.Status.CANCELLED
            queued_at = None
            failure_reason = RoutingWhatsAppErrorCode.TEMPLATE_NOT_CONFIGURED
        elif cls._recent_recipient_message(recipient, template_name, routing_request.id):
            status = RoutingWhatsAppMessage.Status.CANCELLED
            queued_at = None
            failure_reason = RoutingWhatsAppErrorCode.DUPLICATE_RECIPIENT_24H

        if not cls._has_no_emoji(template_payload):
            status = RoutingWhatsAppMessage.Status.FAILED
            queued_at = None
            failure_reason = "TEMPLATE_PAYLOAD_CONTAINS_UNSUPPORTED_CHARACTERS"

        try:
            with transaction.atomic():
                message, created = RoutingWhatsAppMessage.objects.get_or_create(
                    idempotency_key=idempotency_key,
                    defaults={
                        "routing_request": routing_request,
                        "recipient_phone": recipient or "",
                        "template_name": template_name,
                        "template_language": template_language or "en",
                        "template_payload": template_payload,
                        "status": status,
                        "queued_at": queued_at,
                        "failure_reason": failure_reason,
                    },
                )
                if not created and message.status not in ACTIVE_WHATSAPP_STATUSES:
                    message.recipient_phone = recipient or message.recipient_phone
                    message.template_name = template_name
                    message.template_language = template_language or "en"
                    message.template_payload = template_payload
                    message.status = status
                    message.queued_at = queued_at
                    message.failure_reason = failure_reason
                    message.save(update_fields=[
                        "recipient_phone",
                        "template_name",
                        "template_language",
                        "template_payload",
                        "status",
                        "queued_at",
                        "failure_reason",
                        "updated_at",
                    ])
        except IntegrityError:
            message = RoutingWhatsAppMessage.objects.get(idempotency_key=idempotency_key)

        event_type = RoutingEvent.EventType.WHATSAPP_QUEUED if message.status == RoutingWhatsAppMessage.Status.QUEUED else RoutingEvent.EventType.WHATSAPP_FAILED
        if not routing_request.events.filter(event_type=event_type, metadata__idempotency_key=idempotency_key).exists():
            cls._event(
                routing_request,
                event_type,
                metadata={
                    "idempotency_key": idempotency_key,
                    "status": message.status,
                    "recipient": mask_phone(message.recipient_phone),
                    "failure_reason": message.failure_reason,
                    "dry_run": getattr(settings, "CALL_ROUTING_DRY_RUN", True),
                    "whatsapp_enabled": getattr(settings, "ENABLE_CALL_ROUTING_WHATSAPP", False),
                },
            )
        if (
            message.status == RoutingWhatsAppMessage.Status.QUEUED
            and getattr(settings, "ENABLE_CALL_ROUTING", False)
            and not getattr(settings, "CALL_ROUTING_DRY_RUN", True)
            and getattr(settings, "ENABLE_CALL_ROUTING_WHATSAPP", False)
        ):
            from apps.callrouting.tasks import send_routing_whatsapp_message

            transaction.on_commit(lambda: send_routing_whatsapp_message.apply_async(args=(str(message.id),), ignore_result=True))
        return message


class RoutingWhatsAppWebhookService:
    """Link DoubleTick status updates back to RoutingWhatsAppMessage."""

    STATUS_MAP = {
        "sent": RoutingWhatsAppMessage.Status.SENT,
        "delivered": RoutingWhatsAppMessage.Status.DELIVERED,
        "read": RoutingWhatsAppMessage.Status.READ,
        "failed": RoutingWhatsAppMessage.Status.FAILED,
    }

    @classmethod
    def sync_from_doubletick_message(cls, doubletick_message):
        if not doubletick_message:
            return None
        provider_ids = [doubletick_message.message_id, doubletick_message.dt_message_id]
        routing_message = RoutingWhatsAppMessage.objects.filter(
            provider_message_id__in=[value for value in provider_ids if value]
        ).first()
        if not routing_message:
            routing_message = getattr(doubletick_message, "routing_whatsapp_message", None)
        if not routing_message:
            return None

        new_status = cls.STATUS_MAP.get(doubletick_message.status)
        if not new_status:
            return routing_message
        routing_message.doubletick_message = doubletick_message
        routing_message.status = new_status
        routing_message.sent_at = doubletick_message.sent_at or routing_message.sent_at
        routing_message.delivered_at = doubletick_message.delivered_at or routing_message.delivered_at
        routing_message.read_at = doubletick_message.read_at or routing_message.read_at
        routing_message.failed_at = doubletick_message.failed_at or routing_message.failed_at
        routing_message.failure_reason = doubletick_message.failure_reason or routing_message.failure_reason
        routing_message.provider_payload = doubletick_message.raw_payload or routing_message.provider_payload
        routing_message.save(update_fields=[
            "doubletick_message",
            "status",
            "sent_at",
            "delivered_at",
            "read_at",
            "failed_at",
            "failure_reason",
            "provider_payload",
            "updated_at",
        ])
        return routing_message

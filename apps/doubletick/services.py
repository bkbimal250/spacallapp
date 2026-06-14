from django.db import transaction
from django.db.models import Q

from .assignment import assign_lead_to_user_or_device, find_matching_branch
from .integrations.doubletick import (
    get_event_id,
    get_event_type,
    normalize_phone,
    parse_doubletick_payload,
)
from .models import DoubleTickLead, DoubleTickLeadActivity, DoubleTickWebhookLog


def _find_duplicate(parsed):
    checks = Q()
    normalized_phone = parsed.get("normalized_phone")
    chat_id = parsed.get("doubletick_chat_id")
    message_id = parsed.get("doubletick_message_id")

    if normalized_phone and message_id:
        checks |= Q(normalized_phone=normalized_phone, doubletick_message_id=message_id)
    if normalized_phone and chat_id:
        checks |= Q(normalized_phone=normalized_phone, doubletick_chat_id=chat_id)
    if message_id:
        checks |= Q(doubletick_message_id=message_id)

    if not checks:
        return None
    return DoubleTickLead.objects.filter(checks, is_duplicate=False).order_by("-created_at").first()


def send_lead_notification(lead):
    """
    Send an FCM notification through the existing NotificationService.

    NotificationService already handles missing tokens and logs failures, so the
    DoubleTick integration can call it without duplicating FCM behavior.
    """
    recipient = lead.assigned_user or lead.assigned_device
    if not recipient:
        return False

    try:
        from apps.notifications.services import NotificationService
    except Exception:
        return False

    name = lead.customer_name or lead.whatsapp_name or lead.phone_number
    area = lead.area or (lead.assigned_branch.area if lead.assigned_branch else "")
    service = lead.service_name or "WhatsApp inquiry"
    body_parts = [part for part in [name, area, service] if part]

    return NotificationService.send_push(
        recipient=recipient,
        title="New WhatsApp Lead",
        body=" - ".join(body_parts),
        notification_type="system",
        data={"lead_id": str(lead.id), "source": "doubletick"},
    )


@transaction.atomic
def create_or_update_lead_from_webhook(payload):
    """
    Persist a DoubleTick webhook as a CRM lead.

    A webhook log is written first, then the lead is parsed, de-duplicated,
    assigned, activity-logged, and notified. Processing errors are stored in the
    webhook log before being raised to the API layer.
    """
    event_type = get_event_type(payload)
    event_id = get_event_id(payload)
    webhook_log = DoubleTickWebhookLog.objects.create(
        event_type=event_type,
        doubletick_event_id=str(event_id or "") or None,
        payload=payload,
    )

    try:
        parsed = parse_doubletick_payload(payload)
        duplicate = _find_duplicate(parsed)

        if duplicate:
            # Duplicate payloads should not create another lead. The webhook is
            # still linked to the existing lead for audit/replay visibility.
            webhook_log.processed = True
            webhook_log.lead = duplicate
            webhook_log.save(update_fields=["processed", "lead", "updated_at"])
            DoubleTickLeadActivity.objects.create(
                lead=duplicate,
                action=DoubleTickLeadActivity.Action.NOTE,
                note="Duplicate DoubleTick webhook received.",
                metadata={"event_type": event_type, "webhook_log": str(webhook_log.id)},
            )
            return duplicate, webhook_log

        lead = DoubleTickLead.objects.create(
            **parsed,
            status=DoubleTickLead.Status.NEW,
        )

        DoubleTickLeadActivity.objects.create(
            lead=lead,
            action=DoubleTickLeadActivity.Action.CREATED,
            note="Lead created from DoubleTick webhook.",
            metadata={"event_type": event_type, "duplicate": False},
        )

        lead.assigned_branch = find_matching_branch(lead.city, lead.area)
        lead = assign_lead_to_user_or_device(lead)

        action = DoubleTickLeadActivity.Action.ASSIGNED if lead.status == DoubleTickLead.Status.ASSIGNED else DoubleTickLeadActivity.Action.FAILED
        DoubleTickLeadActivity.objects.create(
            lead=lead,
            user=lead.assigned_user,
            device=lead.assigned_device,
            action=action,
            note="Lead assignment completed." if lead.status == DoubleTickLead.Status.ASSIGNED else "No matching branch/user/device found.",
            metadata={"assigned_branch": str(lead.assigned_branch_id) if lead.assigned_branch_id else None},
        )

        if lead.status == DoubleTickLead.Status.ASSIGNED:
            send_lead_notification(lead)

        webhook_log.processed = True
        webhook_log.lead = lead
        webhook_log.save(update_fields=["processed", "lead", "updated_at"])
        return lead, webhook_log
    except Exception as exc:
        webhook_log.error_message = str(exc)
        webhook_log.save(update_fields=["error_message", "updated_at"])
        raise

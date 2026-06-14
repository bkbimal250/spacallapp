import re

from django.conf import settings


def normalize_phone(phone):
    """
    Normalize phone numbers for duplicate checks and lookup.

    For Indian numbers we keep a stable +91XXXXXXXXXX format when 10 digits are
    available. The original display value is still saved separately on the lead.
    """
    digits = re.sub(r"\D", "", str(phone or ""))
    if not digits:
        return ""
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[-10:]
    elif len(digits) > 10:
        digits = digits[-10:]
    if len(digits) == 10:
        return f"+91{digits}"
    return digits


def first_value(payload, paths, default=""):
    """
    Read the first non-empty value from several possible nested payload paths.

    DoubleTick webhook field names can vary, so parsing is defensive and avoids
    failing when optional keys are absent.
    """
    for path in paths:
        value = payload
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        if value not in (None, ""):
            return value
    return default


def get_event_type(payload):
    """Return a stable event type label for webhook audit logs."""
    return str(first_value(payload, ["event", "event_type", "eventType", "type"], default="message"))


def get_event_id(payload):
    """Return the provider event id if DoubleTick sends one."""
    event_id = first_value(payload, ["id", "event_id", "eventId", "data.id"])
    return str(event_id or "") or None


def parse_doubletick_payload(payload):
    """
    Extract CRM lead fields from flexible DoubleTick webhook payloads.

    Unknown fields are intentionally ignored here but the full raw payload is
    stored on the lead and webhook log for future provider-specific mapping.
    """
    customer_name = first_value(payload, [
        "customer.name",
        "contact.name",
        "data.customer.name",
        "data.contact.name",
        "name",
        "customerName",
    ])
    whatsapp_name = first_value(payload, [
        "customer.whatsappName",
        "customer.whatsapp_name",
        "contact.whatsappName",
        "profile.name",
        "whatsapp_name",
    ], default=customer_name)
    phone_number = first_value(payload, [
        "customer.phone",
        "customer.phone_number",
        "contact.phone",
        "contact.phone_number",
        "data.customer.phone",
        "data.contact.phone",
        "phone",
        "phone_number",
        "mobile",
        "from",
        "to",
    ])
    message = first_value(payload, [
        "message.text",
        "message.body",
        "data.message.text",
        "data.message.body",
        "text",
        "body",
        "lastMessage",
        "message",
    ])

    city = first_value(payload, [
        "city",
        "customer.city",
        "contact.city",
        "data.city",
        "customFields.city",
    ])
    area = first_value(payload, [
        "area",
        "customer.area",
        "contact.area",
        "data.area",
        "customFields.area",
        "location.area",
    ])
    service_name = first_value(payload, [
        "service",
        "service_name",
        "customFields.service",
        "customFields.service_name",
        "campaign.service",
    ])
    source_ad = first_value(payload, [
        "source_ad",
        "sourceAd",
        "ad.name",
        "campaign.name",
        "source",
    ])

    return {
        "customer_name": str(customer_name or ""),
        "whatsapp_name": str(whatsapp_name or ""),
        "phone_number": str(phone_number or ""),
        "normalized_phone": normalize_phone(phone_number),
        "message": str(message or ""),
        "city": str(city or ""),
        "area": str(area or ""),
        "service_name": str(service_name or ""),
        "source_ad": str(source_ad or ""),
        "doubletick_customer_id": str(first_value(payload, [
            "customer.id",
            "customer.customerId",
            "data.customer.id",
            "doubletick_customer_id",
            "customerId",
        ]) or ""),
        "doubletick_chat_id": str(first_value(payload, [
            "chat.id",
            "chatId",
            "data.chat.id",
            "conversation.id",
            "doubletick_chat_id",
        ]) or ""),
        "doubletick_message_id": str(first_value(payload, [
            "message.id",
            "messageId",
            "data.message.id",
            "doubletick_message_id",
            "dtMessageId",
        ]) or ""),
        "raw_payload": payload,
    }


def classify_webhook_event(payload):
    """
    Classify provider payloads into the CRM processing buckets.

    Status-only events update local messages and must not create conversations
    or distributable leads.
    """
    event_type = get_event_type(payload).upper()
    message_status = str(first_value(payload, [
        "status",
        "message.status",
        "data.status",
        "eventStatus",
    ]) or "").upper()
    origin = str(first_value(payload, [
        "lastMessageOrigin",
        "message.origin",
        "origin",
        "data.lastMessageOrigin",
    ]) or "").upper()

    if event_type in ["SENT", "DELIVERED", "READ", "FAILED"] or message_status in ["SENT", "DELIVERED", "READ", "FAILED"]:
        return "outbound_message_status"
    if origin == "CUSTOMER" or first_value(payload, ["from", "customer.phone", "contact.phone", "phone", "to"]):
        return "inbound_message"
    if event_type in ["CUSTOMER_CUSTOM_FIELD_UPDATED", "CUSTOMER_FIELD_UPDATED"]:
        return "customer_custom_field_updated"
    if event_type in ["CHAT_ASSIGNED"]:
        return "chat_assigned"
    if event_type in ["CHAT_UNASSIGNED"]:
        return "chat_unassigned"
    if event_type in ["CONVERSATION_CLOSED", "CHAT_CLOSED"]:
        return "conversation_closed"
    return "unknown"


class DoubleTickClient:
    """
    Minimal holder for DoubleTick API settings.

    Outgoing template/message calls are intentionally not implemented yet. This
    keeps the receiving-leads phase ready for future outbound work without
    adding unused HTTP behavior today.
    """

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key if api_key is not None else getattr(settings, "DOUBLETICK_API_KEY", "")
        self.base_url = (base_url if base_url is not None else getattr(settings, "DOUBLETICK_BASE_URL", "")).rstrip("/")

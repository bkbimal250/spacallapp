import json
import logging
import re
import urllib.error
import urllib.request
from difflib import SequenceMatcher

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.branches.models import Branch
from apps.devices.models import Device
from apps.doubletick.integrations.doubletick import first_value, normalize_phone
from apps.doubletick.models import (
    DoubleTickActivity,
    DoubleTickAreaAlias,
    DoubleTickConversation,
    DoubleTickDistributionAudit,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadAssignment,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
)
from apps.doubletick.services import LeadDistributionService, normalize_area_text

from .models import (
    Bot,
    BotApiCallLog,
    BotExecutionLog,
    BotFallbackRule,
    BotFlow,
    BotIntegration,
    BotNode,
    BotNodeOption,
    BotSession,
    BotSessionVariable,
    BotSheetSyncLog,
    BotTrigger,
)


logger = logging.getLogger(__name__)

GENERIC_NON_LOCATION_TEXT = {
    "hello",
    "hi",
    "hey",
    "hii",
    "hiii",
    "ok",
    "okay",
    "namaste",
    "नमस्ते",
    "hindi me message kijiye",
    "hindi mein message kijiye",
    "call me",
}

JOB_KEYWORDS = {"job", "work", "naukri", "काम", "जॉब", "काम चाहिए"}
BOOKING_KEYWORDS = {"booking", "book", "spa", "massage", "service"}
SUPPORT_KEYWORDS = {"support", "help", "complaint", "issue"}


def _digits_only(value):
    return re.sub(r"\D", "", str(value or ""))


def _is_generic_text(value):
    normalized = normalize_area_text(value)
    return not normalized or normalized in {normalize_area_text(item) for item in GENERIC_NON_LOCATION_TEXT}


def _detect_language(text):
    if re.search(r"[\u0900-\u097f]", text or ""):
        return "hi"
    return "hinglish" if re.search(r"\b(kijiye|chahiye|hai|nahi|mein|me)\b", (text or "").lower()) else "en"


def _detect_intent(text):
    normalized = normalize_area_text(text)
    if any(normalize_area_text(item) in normalized for item in JOB_KEYWORDS):
        return "job_inquiry"
    if any(normalize_area_text(item) in normalized for item in BOOKING_KEYWORDS):
        return "booking_inquiry"
    if any(normalize_area_text(item) in normalized for item in SUPPORT_KEYWORDS):
        return "support"
    return "unclear"


def _auth_headers():
    api_key = getattr(settings, "DOUBLETICK_API_KEY", "")
    auth_header = getattr(settings, "DOUBLETICK_AUTH_HEADER", "Authorization") or "Authorization"
    auth_scheme = getattr(settings, "DOUBLETICK_AUTH_SCHEME", "Bearer")
    auth_value = api_key if not auth_scheme else f"{auth_scheme} {api_key}"
    return {"Content-Type": "application/json", auth_header: auth_value}


class DoubleTickOutboundService:
    """Reusable DoubleTick sender that always records the local message first."""

    @staticmethod
    def _url(endpoint_setting, default_endpoint):
        base_url = getattr(settings, "DOUBLETICK_BASE_URL", "https://public.doubletick.io").rstrip("/")
        endpoint = getattr(settings, endpoint_setting, default_endpoint)
        return endpoint if str(endpoint).startswith(("http://", "https://")) else f"{base_url}/{str(endpoint).lstrip('/')}"

    @staticmethod
    def save_outbound_message(to, from_waba, text, lead=None, conversation=None, origin="bot", message_type="text", interactive_payload=None, raw_payload=None):
        conversation = conversation or (lead.conversation if lead else None)
        customer = conversation.customer if conversation else (lead.customer if lead else None)
        now = timezone.now()
        return DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=lead,
            customer=customer,
            dt_message_id="",
            message_id="",
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin=origin,
            message_type=message_type,
            text=text or "",
            interactive_payload=interactive_payload or {},
            status=DoubleTickMessage.Status.QUEUED,
            sender_display_name="Bot" if origin == DoubleTickMessage.Origin.BOT else "",
            customer_number=to,
            waba_number=from_waba,
            message_timestamp=now,
            sent_at=now,
            raw_payload=raw_payload or {},
        )

    @staticmethod
    def _post(url, payload):
        if not getattr(settings, "DOUBLETICK_API_KEY", ""):
            return {"configured": False, "body": "", "status_code": None}
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=_auth_headers(),
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return {"configured": True, "status_code": response.status, "body": response.read().decode("utf-8")}

    @staticmethod
    def _finish_message(message, response):
        if not response.get("configured"):
            message.raw_payload = response
            message.status = DoubleTickMessage.Status.QUEUED
            message.failure_reason = "DoubleTick API key is not configured; message saved locally."
            message.save(update_fields=["raw_payload", "status", "failure_reason", "updated_at"])
            return message
        message.status = DoubleTickMessage.Status.SENT
        message.raw_payload = response
        try:
            parsed = json.loads(response.get("body") or "{}")
            provider_id = first_value(parsed, ["messageId", "id", "data.messageId", "message.id"])
            if provider_id:
                message.message_id = str(provider_id)
                message.dt_message_id = str(provider_id)
        except ValueError:
            pass
        message.save(update_fields=["status", "raw_payload", "message_id", "dt_message_id", "updated_at"])
        return message

    @staticmethod
    def handle_api_error(message, exc):
        message.status = DoubleTickMessage.Status.FAILED
        message.failed_at = timezone.now()
        message.failure_reason = str(exc)
        message.save(update_fields=["status", "failed_at", "failure_reason", "updated_at"])
        return message

    @staticmethod
    def send_text(to, from_waba, text, lead=None, conversation=None, origin="bot"):
        message = DoubleTickOutboundService.save_outbound_message(to, from_waba, text, lead, conversation, origin, "text")
        payload = {"to": _digits_only(to), "message": text, "messageType": "TEXT"}
        if from_waba:
            payload["wabaNumber"] = _digits_only(from_waba)
        try:
            return DoubleTickOutboundService._finish_message(
                message,
                DoubleTickOutboundService._post(DoubleTickOutboundService._url("DOUBLETICK_SEND_TEXT_ENDPOINT", "/whatsapp/message/text"), payload),
            )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            return DoubleTickOutboundService.handle_api_error(message, exc)

    @staticmethod
    def send_interactive_buttons(to, from_waba, body, buttons, lead=None, conversation=None):
        payload = {"to": _digits_only(to), "body": body, "buttons": buttons, "messageType": "INTERACTIVE_BUTTONS"}
        if from_waba:
            payload["wabaNumber"] = _digits_only(from_waba)
        message = DoubleTickOutboundService.save_outbound_message(
            to, from_waba, body, lead, conversation, DoubleTickMessage.Origin.BOT, "interactive_buttons", {"buttons": buttons}, payload
        )
        try:
            return DoubleTickOutboundService._finish_message(
                message,
                DoubleTickOutboundService._post(DoubleTickOutboundService._url("DOUBLETICK_SEND_INTERACTIVE_ENDPOINT", "/whatsapp/message/interactive"), payload),
            )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            return DoubleTickOutboundService.handle_api_error(message, exc)

    @staticmethod
    def send_interactive_list(to, from_waba, header, body, sections, button_text="Select", lead=None, conversation=None):
        payload = {
            "to": _digits_only(to),
            "header": header,
            "body": body,
            "sections": sections,
            "buttonText": button_text,
            "messageType": "INTERACTIVE_LIST",
        }
        if from_waba:
            payload["wabaNumber"] = _digits_only(from_waba)
        message = DoubleTickOutboundService.save_outbound_message(
            to, from_waba, body, lead, conversation, DoubleTickMessage.Origin.BOT, "interactive_list", {"header": header, "sections": sections}, payload
        )
        try:
            return DoubleTickOutboundService._finish_message(
                message,
                DoubleTickOutboundService._post(DoubleTickOutboundService._url("DOUBLETICK_SEND_INTERACTIVE_ENDPOINT", "/whatsapp/message/interactive"), payload),
            )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            return DoubleTickOutboundService.handle_api_error(message, exc)

    @staticmethod
    def send_template(to, from_waba, template_name, language, variables, lead=None, conversation=None):
        payload = {"to": _digits_only(to), "templateName": template_name, "language": language, "variables": variables or {}}
        if from_waba:
            payload["wabaNumber"] = _digits_only(from_waba)
        message = DoubleTickOutboundService.save_outbound_message(
            to, from_waba, template_name, lead, conversation, DoubleTickMessage.Origin.BOT, "template", payload, payload
        )
        try:
            return DoubleTickOutboundService._finish_message(
                message,
                DoubleTickOutboundService._post(DoubleTickOutboundService._url("DOUBLETICK_SEND_TEMPLATE_ENDPOINT", "/whatsapp/message/template"), payload),
            )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            return DoubleTickOutboundService.handle_api_error(message, exc)


class DynamicLocationService:
    PAGE_SIZE = 9

    @staticmethod
    def cities(search="", state="", limit=None):
        qs = Branch.objects.filter(is_active=True, is_deleted=False).exclude(city="")
        if state:
            qs = qs.filter(state__iexact=state)
        if search:
            qs = qs.filter(city__icontains=search)
        qs = qs.values("city").annotate(branch_count=Count("id")).order_by("city")
        return list(qs[: limit or 200])

    @staticmethod
    def areas(city="", search="", limit=None):
        area_names = []
        if city:
            branch_qs = Branch.objects.filter(is_active=True, is_deleted=False, city__iexact=city).exclude(area="")
            if search:
                branch_qs = branch_qs.filter(area__icontains=search)
            area_names.extend(branch_qs.values_list("area", flat=True).distinct())
            lead_area_qs = DoubleTickLeadArea.objects.filter(is_active=True, is_deleted=False, city__iexact=city)
        else:
            lead_area_qs = DoubleTickLeadArea.objects.filter(is_active=True, is_deleted=False)
        if search:
            lead_area_qs = lead_area_qs.filter(Q(name__icontains=search) | Q(normalized_name__icontains=normalize_area_text(search)))
        area_names.extend(lead_area_qs.values_list("name", flat=True).distinct())
        unique = sorted({item for item in area_names if item})
        return [{"area": item} for item in unique[: limit or 200]]

    @staticmethod
    def branches(city="", area="", limit=None):
        qs = Branch.objects.filter(is_active=True, is_deleted=False)
        if city:
            qs = qs.filter(city__iexact=city)
        if area:
            qs = qs.filter(Q(area__iexact=area) | Q(spa_name__icontains=area) | Q(address__icontains=area))
        return list(qs.order_by("spa_name")[: limit or 200])

    @staticmethod
    def paginate_options(items, label_key, value_key=None, page=1):
        page = max(int(page or 1), 1)
        start = (page - 1) * DynamicLocationService.PAGE_SIZE
        page_items = items[start : start + DynamicLocationService.PAGE_SIZE]
        rows = []
        for item in page_items:
            label = item[label_key] if isinstance(item, dict) else getattr(item, label_key)
            value = item[value_key or label_key] if isinstance(item, dict) else getattr(item, value_key or label_key)
            rows.append({"id": f"{label_key}:{value}", "title": str(label)[:24], "description": ""})
        if len(items) > start + DynamicLocationService.PAGE_SIZE:
            rows.append({"id": f"more:{label_key}:{page + 1}", "title": "More locations", "description": ""})
        rows.append({"id": f"type:{label_key}", "title": "Type your area", "description": ""})
        return rows

    @staticmethod
    def match_area(text, city=""):
        if _is_generic_text(text):
            return None, 0
        normalized = normalize_area_text(text)
        alias_qs = DoubleTickAreaAlias.objects.select_related("lead_area").filter(is_active=True, lead_area__is_active=True)
        if city:
            alias_qs = alias_qs.filter(Q(lead_area__city__iexact=city) | Q(lead_area__city=""))
        exact = alias_qs.filter(normalized_alias=normalized).first()
        if exact:
            return exact.lead_area, 100
        area_qs = DoubleTickLeadArea.objects.filter(is_active=True, is_deleted=False)
        if city:
            area_qs = area_qs.filter(Q(city__iexact=city) | Q(city=""))
        best = (None, 0)
        for area in area_qs:
            score = SequenceMatcher(None, normalized, normalize_area_text(area.name)).ratio()
            if normalized and normalize_area_text(area.name) in normalized:
                score = max(score, 0.92)
            if score > best[1]:
                best = (area, score)
        return (best[0], int(best[1] * 100)) if best[1] >= 0.88 else (None, int(best[1] * 100))


class BotEngine:
    @staticmethod
    def ensure_default_booking_bot():
        bot, _ = Bot.objects.get_or_create(
            slug="default-booking-bot",
            defaults={"name": "Default Booking Bot", "bot_type": Bot.BotType.BOOKING, "is_active": True, "priority": 1000},
        )
        flow = bot.flows.filter(is_active=True).first()
        BotTrigger.objects.get_or_create(
            bot=bot,
            trigger_type=BotTrigger.TriggerType.FIRST_INBOUND,
            is_default=True,
            defaults={"priority": 1000},
        )
        if flow:
            return bot, flow
        flow = BotFlow.objects.create(bot=bot, name="Default Booking Flow", version=1, is_active=True, is_published=True, published_at=timezone.now())
        start = BotNode.objects.create(flow=flow, name="Greeting", node_type=BotNode.NodeType.START, message_text="Namaste! Please select your city.", order=1)
        city = BotNode.objects.create(flow=flow, name="Select City", node_type=BotNode.NodeType.DYNAMIC_CITY_SELECT, message_text="Please select your city.", order=2)
        area = BotNode.objects.create(flow=flow, name="Select Area", node_type=BotNode.NodeType.DYNAMIC_AREA_SELECT, message_text="Please select your area.", order=3)
        branch = BotNode.objects.create(flow=flow, name="Select Branch", node_type=BotNode.NodeType.DYNAMIC_BRANCH_SELECT, message_text="Please select your branch.", order=4)
        assign = BotNode.objects.create(flow=flow, name="Assign Lead", node_type=BotNode.NodeType.ASSIGN_LEAD, message_text="Thank you. Our team will contact you shortly.", order=5)
        start.default_next_node = city
        city.default_next_node = area
        area.default_next_node = branch
        branch.default_next_node = assign
        for node in [start, city, area, branch]:
            node.save(update_fields=["default_next_node", "updated_at"])
        return bot, flow

    @staticmethod
    def find_bot(conversation, lead=None, message=None):
        channel = conversation.channel if conversation else None
        source = getattr(lead, "source_ad", "") if lead else ""
        city = (getattr(lead, "city", "") or getattr(lead, "raw_city", "") or getattr(conversation, "raw_city", "") or "").strip()
        lead_type = (getattr(lead, "raw_service", "") or getattr(lead, "service_name", "") or "").strip()
        message_text = (getattr(message, "text", "") or "").lower()
        triggers = BotTrigger.objects.select_related("bot").filter(is_active=True, bot__is_active=True)
        if channel:
            trigger = triggers.filter(channel=channel).order_by("-priority", "created_at").first()
            if trigger:
                return trigger.bot
        if message_text:
            for trigger in triggers.exclude(keywords=[]).order_by("-priority", "created_at"):
                if any(str(keyword).lower() in message_text for keyword in (trigger.keywords or [])):
                    return trigger.bot
        if source:
            trigger = triggers.filter(source_campaign__iexact=source).order_by("-priority", "created_at").first()
            if trigger:
                return trigger.bot
        if city:
            trigger = triggers.filter(city__iexact=city).order_by("-priority", "created_at").first()
            if trigger:
                return trigger.bot
        if lead_type:
            trigger = triggers.filter(lead_type__iexact=lead_type).order_by("-priority", "created_at").first()
            if trigger:
                return trigger.bot
        trigger = triggers.filter(is_default=True).order_by("-priority", "created_at").first()
        if trigger:
            return trigger.bot
        bot, _flow = BotEngine.ensure_default_booking_bot()
        return bot

    @staticmethod
    def get_flow(bot):
        flow = bot.flows.filter(is_active=True, is_published=True).order_by("-version").first()
        if not flow:
            flow = bot.flows.filter(is_active=True).order_by("-version").first()
        return flow

    @staticmethod
    def get_start_node(flow):
        return flow.nodes.filter(is_active=True, node_type=BotNode.NodeType.START).order_by("order").first() or flow.nodes.filter(is_active=True).order_by("order").first()

    @staticmethod
    def get_or_create_session(conversation, lead, message):
        bot = BotEngine.find_bot(conversation, lead, message)
        flow = BotEngine.get_flow(bot)
        if not flow:
            bot, flow = BotEngine.ensure_default_booking_bot()
        session, created = BotSession.objects.get_or_create(
            conversation=conversation,
            bot=bot,
            status=BotSession.Status.ACTIVE,
            defaults={
                "flow": flow,
                "current_node": BotEngine.get_start_node(flow),
                "customer": conversation.customer,
                "lead": lead,
                "language": _detect_language(message.text if message else ""),
                "last_activity_at": timezone.now(),
            },
        )
        if lead and session.lead_id != lead.id:
            session.lead = lead
        session.last_customer_message = message.text if message else session.last_customer_message
        session.intent = session.intent or _detect_intent(session.last_customer_message)
        session.language = session.language or _detect_language(session.last_customer_message)
        session.last_activity_at = timezone.now()
        session.save()
        return session, created

    @staticmethod
    def _recipient(conversation):
        return conversation.customer.normalized_phone or normalize_phone(conversation.customer.phone_number) or conversation.customer.phone_number

    @staticmethod
    def _from_waba(conversation):
        return conversation.channel.waba_number if conversation.channel else getattr(settings, "DOUBLETICK_SEND_FROM_WABA_NUMBER", "")

    @staticmethod
    def _log(session, node, message, status=BotExecutionLog.Status.STARTED, outbound=None, event="", error="", metadata=None):
        key = BotEngine.idempotency_key(session, node, message)
        log, _ = BotExecutionLog.objects.get_or_create(
            idempotency_key=key,
            defaults={
                "session": session,
                "node": node,
                "conversation": session.conversation,
                "lead": session.lead,
                "incoming_message": message,
                "outbound_message": outbound,
                "status": status,
                "event": event,
                "error_message": error,
                "metadata": metadata or {},
            },
        )
        return log

    @staticmethod
    def idempotency_key(session, node, message):
        message_key = getattr(message, "dt_message_id", "") or getattr(message, "message_id", "") or str(getattr(message, "id", ""))
        return f"{session.id}:{getattr(node, 'id', 'none')}:{message_key}"

    @staticmethod
    def already_replied(session, node, message):
        key = BotEngine.idempotency_key(session, node, message)
        return BotExecutionLog.objects.filter(idempotency_key=key, status__in=[BotExecutionLog.Status.SENT, BotExecutionLog.Status.SKIPPED]).exists()

    @staticmethod
    def handle_incoming_message(conversation, lead, message):
        if not message or message.direction != DoubleTickMessage.Direction.INBOUND:
            return None
        try:
            session, created = BotEngine.get_or_create_session(conversation, lead, message)
            if session.status != BotSession.Status.ACTIVE:
                return session
            node = session.current_node or BotEngine.get_start_node(session.flow)
            if BotEngine.already_replied(session, node, message):
                return session
            BotEngine.process_customer_reply(session, message)
            return BotEngine.run_current_node(session, message, created=created)
        except Exception as exc:
            logger.exception("BotEngine failed for conversation %s", conversation.id if conversation else "")
            try:
                BotExecutionLog.objects.create(conversation=conversation, lead=lead, incoming_message=message, status=BotExecutionLog.Status.FAILED, error_message=str(exc))
            except Exception:
                logger.exception("BotEngine failed to write failure log.")
            return None

    @staticmethod
    def process_customer_reply(session, message):
        text = message.text or ""
        payload = message.interactive_payload or {}
        reply_value = str(first_value(payload, ["id", "payload", "value", "button_reply.id", "list_reply.id"]) or text)
        node = session.current_node
        if not node:
            return
        option = node.options.filter(is_active=True).filter(Q(payload_id=reply_value) | Q(value__iexact=reply_value) | Q(label__iexact=reply_value) | Q(label__iexact=text)).first()
        if option:
            BotEngine.apply_option(session, option, text)
            session.current_node = option.next_node or node.default_next_node or session.current_node
            session.save()
            return
        if str(reply_value).startswith("more:"):
            parts = str(reply_value).split(":")
            session.variables["page"] = int(parts[-1]) if parts[-1].isdigit() else 1
            session.save(update_fields=["variables", "updated_at"])
            return
        dynamic_value = reply_value or text
        if node.node_type == BotNode.NodeType.DYNAMIC_CITY_SELECT:
            BotEngine.select_city(session, dynamic_value)
        elif node.node_type == BotNode.NodeType.DYNAMIC_AREA_SELECT:
            BotEngine.select_area(session, dynamic_value)
        elif node.node_type == BotNode.NodeType.DYNAMIC_BRANCH_SELECT:
            BotEngine.select_branch(session, dynamic_value)
        elif node.node_type == BotNode.NodeType.COLLECT_INPUT:
            key = node.config.get("variable", "input")
            BotEngine.set_variable(session, key, text)
            session.current_node = node.default_next_node or session.current_node
            session.save()
        else:
            session.intent = session.intent or _detect_intent(text)
            session.save(update_fields=["intent", "updated_at"])

    @staticmethod
    def apply_option(session, option, text):
        data = option.metadata or {}
        if data.get("city"):
            session.selected_city = data["city"]
        if data.get("area"):
            session.selected_area = data["area"]
        if data.get("branch_id"):
            session.selected_branch_id = data["branch_id"]
        if data.get("intent"):
            session.intent = data["intent"]

    @staticmethod
    def set_variable(session, key, value):
        session.variables[key] = value
        BotSessionVariable.objects.update_or_create(session=session, key=key, defaults={"value": {"value": value}})

    @staticmethod
    def select_city(session, text):
        value = text.replace("city:", "", 1).strip()
        cities = DynamicLocationService.cities(search=value, limit=5)
        if len(cities) == 1:
            session.selected_city = cities[0]["city"]
            session.variables.pop("page", None)
            session.current_node = session.current_node.default_next_node or session.current_node
            session.save()
            return True
        session.fallback_count += 1
        session.save(update_fields=["fallback_count", "updated_at"])
        return False

    @staticmethod
    def select_area(session, text):
        value = text.replace("area:", "", 1).strip()
        matched_area, confidence = DynamicLocationService.match_area(value, session.selected_city)
        if matched_area:
            session.selected_area = matched_area.name
            BotEngine.set_variable(session, "matched_area_id", str(matched_area.id))
            if session.lead:
                session.lead.raw_city = session.selected_city or session.lead.raw_city
                session.lead.raw_area = matched_area.name
                session.lead.city = session.selected_city or session.lead.city
                session.lead.area = matched_area.name
                session.lead.matched_area = matched_area
                session.lead.status = DoubleTickLead.Status.AVAILABLE
                session.lead.save()
            if session.conversation:
                session.conversation.raw_city = session.selected_city or session.conversation.raw_city
                session.conversation.raw_area = matched_area.name
                session.conversation.matched_area = matched_area
                session.conversation.area_confirmed = True
                session.conversation.requires_manual_attention = False
                session.conversation.status = DoubleTickConversation.Status.QUALIFIED
                session.conversation.pending_reason = ""
                session.conversation.save()
            branches = DynamicLocationService.branches(session.selected_city, matched_area.name, limit=2)
            next_node = session.current_node.default_next_node if session.current_node else None
            if len(branches) == 1:
                session.selected_branch = branches[0]
                BotEngine.assign_lead_to_branch(session, branches[0])
                if next_node and next_node.default_next_node:
                    next_node = next_node.default_next_node
            session.current_node = next_node or session.current_node
            session.save()
            return True
        if confidence < 88:
            BotEngine.mark_fallback(session, "unclear_location")
        return False

    @staticmethod
    def select_branch(session, text):
        value = text.replace("branch:", "", 1).strip()
        branch = None
        if re.match(r"^[0-9a-f-]{32,36}$", value):
            branch = Branch.objects.filter(id=value).first()
        if not branch:
            branch = DynamicLocationService.branches(session.selected_city, session.selected_area).filter(spa_name__iexact=value).first() if hasattr(DynamicLocationService.branches("", ""), "filter") else None
        if not branch:
            for candidate in DynamicLocationService.branches(session.selected_city, session.selected_area, limit=50):
                if normalize_area_text(candidate.spa_name) == normalize_area_text(value):
                    branch = candidate
                    break
        if branch:
            session.selected_branch = branch
            BotEngine.assign_lead_to_branch(session, branch)
            session.current_node = session.current_node.default_next_node or session.current_node
            session.save()
            return True
        BotEngine.mark_fallback(session, "unclear_branch")
        return False

    @staticmethod
    @transaction.atomic
    def assign_lead_to_branch(session, branch):
        lead = session.lead
        if not lead:
            return None
        lead.current_branch = branch
        lead.assigned_branch = branch
        lead.status = DoubleTickLead.Status.AVAILABLE
        lead.save()
        DoubleTickLeadVisibility.objects.get_or_create(lead=lead, branch=branch)
        User = get_user_model()
        for manager in User.objects.filter(role="spa_manager", branch=branch, is_active=True):
            DoubleTickLeadVisibility.objects.get_or_create(lead=lead, branch=branch, user=manager)
        for device in Device.objects.filter(branch=branch, is_active=True, is_blocked=False, is_registered=True):
            DoubleTickLeadVisibility.objects.get_or_create(lead=lead, branch=branch, device=device)
        DoubleTickDistributionAudit.objects.create(
            lead=lead,
            conversation=session.conversation,
            matched_area=lead.matched_area,
            status=DoubleTickDistributionAudit.Status.SUCCESS,
            mapped_branch_count=1,
            visibility_count=lead.visibilities.count(),
            metadata={"selected_branch_id": str(branch.id), "source": "bot"},
        )
        return lead

    @staticmethod
    def mark_fallback(session, reason):
        session.fallback_count += 1
        if session.conversation:
            session.conversation.requires_manual_attention = True
            session.conversation.pending_reason = DoubleTickConversation.PendingReason.OTHER
            session.conversation.save(update_fields=["requires_manual_attention", "pending_reason", "updated_at"])
        if session.lead:
            session.lead.status = DoubleTickLead.Status.UNASSIGNED
            session.lead.save(update_fields=["status", "updated_at"])
        if session.fallback_count >= 3:
            session.status = BotSession.Status.HANDED_OVER
            if session.conversation:
                session.conversation.status = DoubleTickConversation.Status.MANUAL_ATTENTION
                session.conversation.save(update_fields=["status", "updated_at"])
        session.save()

    @staticmethod
    def run_current_node(session, incoming_message, created=False):
        node = session.current_node or BotEngine.get_start_node(session.flow)
        if not node:
            return session
        if BotEngine.already_replied(session, node, incoming_message):
            return session
        text = session.last_customer_message or ""
        if session.intent == "job_inquiry":
            return BotEngine.run_job_handover(session, incoming_message)
        if node.node_type == BotNode.NodeType.START:
            session.current_node = node.default_next_node or node
            session.save(update_fields=["current_node", "updated_at"])
            if node.message_text:
                BotEngine.send_node_text(session, node, incoming_message, node.message_text)
            return BotEngine.run_current_node(session, incoming_message, created=created)
        if node.node_type in [BotNode.NodeType.TEXT_MESSAGE, BotNode.NodeType.QUESTION]:
            BotEngine.send_node_text(session, node, incoming_message, node.message_text)
            session.current_node = node.default_next_node or node
        elif node.node_type == BotNode.NodeType.DYNAMIC_CITY_SELECT:
            BotEngine.send_city_options(session, node, incoming_message)
        elif node.node_type == BotNode.NodeType.DYNAMIC_AREA_SELECT:
            BotEngine.send_area_options(session, node, incoming_message)
        elif node.node_type == BotNode.NodeType.DYNAMIC_BRANCH_SELECT:
            BotEngine.send_branch_options(session, node, incoming_message)
        elif node.node_type in [BotNode.NodeType.ASSIGN_LEAD, BotNode.NodeType.BROADCAST_LEAD, BotNode.NodeType.ROUND_ROBIN_ASSIGN]:
            if session.lead and session.lead.matched_area_id and node.node_type != BotNode.NodeType.ASSIGN_LEAD:
                LeadDistributionService.distribute(session.lead)
            BotEngine.send_node_text(session, node, incoming_message, node.message_text or "Thank you. Our team will contact you shortly.")
            session.status = BotSession.Status.COMPLETED
        elif node.node_type == BotNode.NodeType.MANUAL_HANDOVER:
            BotEngine.mark_fallback(session, "manual_handover")
            BotEngine.send_node_text(session, node, incoming_message, node.message_text or "Our team will help you shortly.")
        elif node.node_type == BotNode.NodeType.API_CALL:
            BotEngine.run_api_call(session, node)
            session.current_node = node.default_next_node or node
        elif node.node_type == BotNode.NodeType.GOOGLE_SHEET_APPEND:
            BotEngine.run_sheet_append(session, node)
            session.current_node = node.default_next_node or node
        elif node.node_type == BotNode.NodeType.END:
            BotEngine.send_node_text(session, node, incoming_message, node.message_text)
            session.status = BotSession.Status.COMPLETED
        else:
            BotEngine.send_node_text(session, node, incoming_message, node.message_text or "Please share your city or area.")
        session.last_activity_at = timezone.now()
        session.save()
        return session

    @staticmethod
    def send_node_text(session, node, incoming_message, text):
        outbound = DoubleTickOutboundService.send_text(
            BotEngine._recipient(session.conversation),
            BotEngine._from_waba(session.conversation),
            text,
            lead=session.lead,
            conversation=session.conversation,
            origin=DoubleTickMessage.Origin.BOT,
        )
        session.last_bot_message = text
        session.save(update_fields=["last_bot_message", "updated_at"])
        log = BotEngine._log(session, node, incoming_message, BotExecutionLog.Status.SENT, outbound=outbound, event="send_text")
        return outbound, log

    @staticmethod
    def _send_list(session, node, incoming_message, header, body, rows):
        outbound = DoubleTickOutboundService.send_interactive_list(
            BotEngine._recipient(session.conversation),
            BotEngine._from_waba(session.conversation),
            header,
            body,
            [{"title": header[:24], "rows": rows}],
            "Select",
            lead=session.lead,
            conversation=session.conversation,
        )
        session.last_bot_message = body
        session.save(update_fields=["last_bot_message", "updated_at"])
        BotEngine._log(session, node, incoming_message, BotExecutionLog.Status.SENT, outbound=outbound, event="send_interactive_list")
        return outbound

    @staticmethod
    def send_city_options(session, node, incoming_message):
        page = session.variables.get("page", 1)
        cities = DynamicLocationService.cities(state=session.selected_state)
        rows = DynamicLocationService.paginate_options(cities, "city", page=page)
        return BotEngine._send_list(session, node, incoming_message, "Select City", node.message_text or "Please select your city.", rows)

    @staticmethod
    def send_area_options(session, node, incoming_message):
        page = session.variables.get("page", 1)
        areas = DynamicLocationService.areas(city=session.selected_city)
        rows = DynamicLocationService.paginate_options(areas, "area", page=page)
        return BotEngine._send_list(session, node, incoming_message, "Select Area", node.message_text or "Please select your area.", rows)

    @staticmethod
    def send_branch_options(session, node, incoming_message):
        branches = DynamicLocationService.branches(session.selected_city, session.selected_area)
        if len(branches) == 1:
            BotEngine.assign_lead_to_branch(session, branches[0])
            session.current_node = node.default_next_node or node
            session.save()
            return None
        rows = [{"id": f"branch:{branch.id}", "title": branch.spa_name[:24], "description": branch.area or branch.city} for branch in branches[:9]]
        rows.append({"id": "type:branch", "title": "Type branch", "description": ""})
        return BotEngine._send_list(session, node, incoming_message, "Select Branch", node.message_text or "Please select your preferred branch.", rows)

    @staticmethod
    def run_job_handover(session, incoming_message):
        session.intent = "job_inquiry"
        session.status = BotSession.Status.HANDED_OVER
        if session.lead:
            session.lead.status = DoubleTickLead.Status.UNASSIGNED
            session.lead.remarks = "\n".join(part for part in [session.lead.remarks, "Bot detected job/work inquiry."] if part)
            session.lead.save(update_fields=["status", "remarks", "updated_at"])
        if session.conversation:
            session.conversation.requires_manual_attention = True
            session.conversation.pending_reason = DoubleTickConversation.PendingReason.OTHER
            session.conversation.save(update_fields=["requires_manual_attention", "pending_reason", "updated_at"])
        session.save()
        BotEngine.send_node_text(session, session.current_node, incoming_message, "Please share your name, city, and work experience. Our team will review your inquiry.")
        return session

    @staticmethod
    def run_api_call(session, node):
        integration_id = node.config.get("integration_id")
        integration = BotIntegration.objects.filter(id=integration_id, is_active=True).first() if integration_id else None
        url = node.config.get("url") or (integration.config.get("url") if integration else "")
        payload = {"session_id": str(session.id), "lead_id": str(session.lead_id or ""), "variables": session.variables}
        log = BotApiCallLog.objects.create(integration=integration, session=session, node=node, url=url, request_payload=payload)
        if not url:
            log.error_message = "No API URL configured."
            log.save(update_fields=["error_message"])
            return log
        try:
            request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method=node.config.get("method", "POST"))
            with urllib.request.urlopen(request, timeout=int(node.config.get("timeout", 10))) as response:
                body = response.read().decode("utf-8")
                log.status_code = response.status
                log.response_payload = json.loads(body or "{}")
                log.success = 200 <= response.status < 300
        except Exception as exc:
            log.error_message = str(exc)
        log.save()
        return log

    @staticmethod
    def run_sheet_append(session, node):
        row = {
            "customer": session.conversation.customer.customer_name if session.conversation and session.conversation.customer else "",
            "phone": session.conversation.customer.phone_number if session.conversation and session.conversation.customer else "",
            "city": session.selected_city,
            "area": session.selected_area,
            "branch": session.selected_branch.spa_name if session.selected_branch else "",
            "message": session.last_customer_message,
            "status": session.status,
            "created_at": timezone.now().isoformat(),
        }
        return BotSheetSyncLog.objects.create(session=session, lead=session.lead, row_payload=row, success=False, error_message="Google Sheets adapter is not configured.")

    @staticmethod
    def manual_send_location_options(lead):
        session = BotSession.objects.filter(lead=lead, status=BotSession.Status.ACTIVE).order_by("-updated_at").first()
        if not session:
            bot = BotEngine.find_bot(lead.conversation, lead, None)
            flow = BotEngine.get_flow(bot) or BotEngine.ensure_default_booking_bot()[1]
            session = BotSession.objects.create(bot=bot, flow=flow, current_node=flow.nodes.filter(node_type=BotNode.NodeType.DYNAMIC_CITY_SELECT).first(), conversation=lead.conversation, customer=lead.customer, lead=lead, status=BotSession.Status.ACTIVE)
        node = session.flow.nodes.filter(node_type=BotNode.NodeType.DYNAMIC_CITY_SELECT).first() or session.current_node
        session.current_node = node
        session.save(update_fields=["current_node", "updated_at"])
        fake_message = lead.messages.filter(direction=DoubleTickMessage.Direction.INBOUND).order_by("-created_at").first()
        return BotEngine.send_city_options(session, node, fake_message)

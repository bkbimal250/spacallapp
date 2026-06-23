import hashlib
import json
import logging
import re
import urllib.error
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.branches.models import Branch
from apps.devices.models import Device

from .channel_setup import find_channel_for_waba_number, normalize_waba_number
from .integrations.doubletick import (
    classify_webhook_event,
    first_value,
    get_event_id,
    get_event_type,
    normalize_phone,
    parse_doubletick_payload,
)
from .models import (
    DoubleTickActivity,
    DoubleTickAreaAlias,
    DoubleTickChannel,
    DoubleTickConversation,
    DoubleTickCustomer,
    DoubleTickDistributionAudit,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadAssignment,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
    DoubleTickTeamMemberMapping,
    DoubleTickWebhookLog,
)

logger = logging.getLogger(__name__)


GREETING_WORDS = {
    "acha",
    "accha",
    "call me",
    "can i get more info",
    "charges",
    "details",
    "good evening",
    "good morning",
    "he",
    "hell",
    "hello",
    "hello sir",
    "helloo",
    "helo",
    "hey",
    "hi",
    "hi sir",
    "hii",
    "hiii",
    "hmm",
    "hy",
    "hyy",
    "information",
    "more info",
    "namaste",
    "no",
    "ok",
    "okay",
    "please call",
    "price",
    "rate",
    "yes",
    "à¤¨à¤®à¤¸à¥à¤¤à¥‡",
    "à¤¨à¤®à¤¸à¥à¤•à¤¾à¤°",
    "à¤¹à¥‡à¤²à¥‹",
    "à¤¹à¤¾à¤¯",
    "à¤°à¤¾à¤® à¤°à¤¾à¤®",
}
JOB_INQUIRY_WORDS = {
    "job",
    "job chahiye",
    "kaam chahiye",
    "mujhe job chahiye",
    "naukri",
    "salary",
    "vacancy",
    "work",
    "à¤•à¤¾à¤®",
    "à¤•à¤¾à¤® à¤šà¤¾à¤¹à¤¿à¤",
    "à¤¨à¥Œà¤•à¤°à¥€ à¤šà¤¾à¤¹à¤¿à¤",
}
SERVICE_ACTION_WORDS = {
    "explore services",
    "service",
    "services",
}
GENERIC_NON_LOCATION_PHRASES = {
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
    "please message in hindi",
}
LOCATION_REQUEST_MESSAGE = getattr(
    settings,
    "DOUBLETICK_LOCATION_REQUEST_MESSAGE",
    "Just Provide Me Your Location So That I Can Help You With Booking...\n\nबस मुझे अपना स्थान बताएं ताकि मैं बुकिंग में आपकी मदद कर सकूं..",
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


def normalize_area_text(value):
    """Normalize free-form area text for alias matching."""
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return re.sub(r"[^0-9a-z\u0900-\u097f ]+", "", text)


def _is_generic_non_location_text(value):
    normalized = normalize_area_text(value)
    if not normalized:
        return True
    if normalized in {normalize_area_text(item) for item in GENERIC_NON_LOCATION_PHRASES}:
        return True
    return any(fragment in normalized for fragment in ["message kijiye", "hindi me", "hindi mein"])


def _contains_normalized(haystack, needle):
    haystack_norm = normalize_area_text(haystack)
    needle_norm = normalize_area_text(needle)
    return bool(haystack_norm and needle_norm and (needle_norm in haystack_norm or haystack_norm in needle_norm))


def _timestamp_from_payload(payload):
    value = first_value(payload, ["timestamp", "createdAt", "receivedAt", "message.timestamp", "data.timestamp", "statusTimestamp"])
    if not value:
        return timezone.now()
    if isinstance(value, (int, float)):
        return timezone.datetime.fromtimestamp(value / 1000 if value > 9999999999 else value, tz=timezone.utc)
    if isinstance(value, str):
        parsed = parse_datetime(value)
        if parsed:
            return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed, timezone=timezone.utc)
    return timezone.now()


def _status_to_message_status(provider_status):
    status_value = str(provider_status or "").lower()
    return status_value if status_value in DoubleTickMessage.Status.values else DoubleTickMessage.Status.RECEIVED


def _normalized_lookup_values(value):
    raw = str(value or "").strip()
    normalized = normalize_phone(raw)
    values = {raw}
    if normalized:
        values.add(normalized)
        values.add(normalized.replace("+", ""))
    return [item for item in values if item]


def _channel_from_waba_number(waba_number):
    return find_channel_for_waba_number(waba_number)


def _provider_message_type(payload):
    return str(first_value(payload, ["message.type", "messageType", "data.message.type"], default="text") or "text").lower()


def _message_text(payload):
    return str(first_value(payload, [
        "message.text",
        "message.body",
        "message.button.text",
        "message.interactive.button_reply.title",
        "message.interactive.list_reply.title",
        "interactive.button_reply.title",
        "interactive.list_reply.title",
        "data.message.text",
        "data.message.body",
        "text",
        "body",
    ]) or "")


def _digits_only(value):
    """DoubleTick send APIs expect WhatsApp numbers without display symbols."""
    return re.sub(r"\D", "", str(value or ""))


def _resolve_outbound_sender(sent_by, assigned_to, channel=None):
    """
    Resolve DoubleTick sender identifiers into a stable origin and display name.

    DoubleTick sends associate phone/user identifiers in status events. The CRM
    keeps the raw identifiers and uses optional mappings for readable names.
    """
    sent_by_value = str(sent_by or "").strip()
    assigned_to_value = str(assigned_to or "").strip()
    upper_sent_by = sent_by_value.upper()
    if upper_sent_by == "BOT":
        return DoubleTickMessage.Origin.BOT, "Bot", None
    if upper_sent_by == "API":
        return DoubleTickMessage.Origin.API, "API", None

    identifiers = [sent_by_value, assigned_to_value]
    phone_values = []
    for value in identifiers:
        phone_values.extend(_normalized_lookup_values(value))

    mapping_q = Q()
    for value in identifiers:
        if value:
            mapping_q |= Q(doubletick_user_id=value)
    for value in phone_values:
        mapping_q |= Q(doubletick_phone=value)

    if mapping_q:
        mappings = DoubleTickTeamMemberMapping.objects.filter(mapping_q, is_active=True)
        if channel:
            mappings = mappings.filter(Q(channel=channel) | Q(channel__isnull=True)).order_by("-channel_id", "display_name")
        mapping = mappings.select_related("crm_user").first()
        if mapping:
            return DoubleTickMessage.Origin.AGENT, mapping.display_name or getattr(mapping.crm_user, "full_name", "") or "Associate", mapping.crm_user

    if sent_by_value or assigned_to_value:
        return DoubleTickMessage.Origin.AGENT, "Associate", None
    return DoubleTickMessage.Origin.SYSTEM, "System", None


def _activity(**kwargs):
    """Create an immutable timeline entry without leaking provider secrets."""
    return DoubleTickActivity.objects.create(**kwargs)


class CRMLocationMatchEngine:
    """Match inbound raw location text against the normalized CRM locations app data."""

    @staticmethod
    def normalize_text(value):
        if not value:
            return ""
        try:
            from apps.locations.models import normalize_location_name

            return normalize_location_name(value)
        except Exception:
            return normalize_area_text(value)

    @staticmethod
    def find_area(raw_area, raw_city="", group_id=None):
        normalized_area = CRMLocationMatchEngine.normalize_text(raw_area)
        if not normalized_area:
            return None

        try:
            from apps.locations.models import Area, AreaAlias

            qs = Area.objects.filter(is_deleted=False, is_active=True)
            if group_id:
                qs = qs.filter(area_groups__group_id=group_id, area_groups__is_deleted=False)

            if raw_city:
                normalized_city = CRMLocationMatchEngine.normalize_text(raw_city)
                qs = qs.filter(
                    Q(city__normalized_name=normalized_city)
                    | Q(city__aliases__normalized_alias=normalized_city)
                )

            area = qs.filter(normalized_name=normalized_area).select_related("city", "city__state").first()
            if area:
                return area

            alias_qs = AreaAlias.objects.filter(is_deleted=False, is_active=True, normalized_alias=normalized_area)
            if raw_city:
                alias_qs = alias_qs.filter(
                    Q(area__city__normalized_name=normalized_city)
                    | Q(area__city__aliases__normalized_alias=normalized_city)
                )
            if group_id:
                alias_qs = alias_qs.filter(area__area_groups__group_id=group_id, area__area_groups__is_deleted=False)

            alias = alias_qs.select_related("area", "area__city", "area__city__state").first()
            return alias.area if alias else None
        except Exception:
            return None

    @staticmethod
    def ensure_area_from_location_area(location_area, raw_alias=None, channel=None):
        if not location_area:
            return None

        normalized = CRMLocationMatchEngine.normalize_text(location_area.name)
        if not normalized:
            return None

        lead_area = DoubleTickLeadArea.objects.filter(
            location_area=location_area,
            is_deleted=False,
        ).order_by("-is_active", "priority", "created_at").first()

        if not lead_area:
            city_name = location_area.city.name if location_area.city else ""
            lead_area = DoubleTickLeadArea.objects.filter(
                location_area__isnull=True,
                normalized_name=normalized,
                city__iexact=city_name,
                is_deleted=False,
            ).order_by("-is_active", "priority", "created_at").first()
            if lead_area:
                lead_area.location_area = location_area
                lead_area.save(update_fields=["location_area", "updated_at"])

        if not lead_area:
            lead_area = DoubleTickLeadArea.objects.create(
                location_area=location_area,
                normalized_name=normalized,
                city=location_area.city.name if location_area.city else "",
                name=location_area.name,
                state=location_area.city.state.name if location_area.city and location_area.city.state else "",
                is_active=True,
                description="Auto-created from CRM location area.",
            )

        if raw_alias:
            alias_normalized = normalize_area_text(raw_alias)
            if alias_normalized:
                DoubleTickAreaAlias.objects.get_or_create(
                    lead_area=lead_area,
                    normalized_alias=alias_normalized,
                    defaults={
                        "alias": raw_alias,
                        "channel": channel,
                        "created_from_manual_mapping": True,
                    },
                )

        try:
            from apps.locations.models import BranchCoverageArea
            from django.contrib.contenttypes.models import ContentType

            branches = list(
                Branch.objects.filter(location_area=location_area, is_active=True, is_deleted=False)
            )
            if not branches:
                branch_ct = ContentType.objects.get_for_model(Branch)
                coverage_qs = BranchCoverageArea.objects.filter(
                    is_deleted=False,
                    is_active=True,
                    area=location_area,
                    content_type=branch_ct,
                )
                for coverage in coverage_qs.select_related("content_type"):
                    branch = getattr(coverage, "branch", None)
                    if branch and branch.is_active and not branch.is_deleted:
                        branches.append(branch)

            for branch in branches:
                DoubleTickLeadAreaBranch.objects.get_or_create(
                    lead_area=lead_area,
                    branch=branch,
                    defaults={
                        "is_active": True,
                        "receives_leads": True,
                        "notes": "Auto-created from CRM location coverage.",
                    },
                )
        except Exception:
            pass

        return lead_area

    @staticmethod
    def _base_result(text):
        return {
            "classification": "unknown",
            "confidence": 0.0,
            "reason": "",
            "state": None,
            "city": None,
            "location_group": None,
            "area": None,
            "branch": None,
            "raw_city": "",
            "raw_group": "",
            "raw_area": "",
            "raw_branch": "",
            "raw_service": "",
            "matched_area": None,
            "current_branch": None,
            "should_request_location": False,
            "input": str(text or "").strip(),
        }

    @staticmethod
    def _active_locations():
        from apps.locations.models import Area, AreaAlias, City, CityAlias, LocationGroup, State

        return {
            "states": State.objects.filter(is_deleted=False, is_active=True),
            "cities": City.objects.filter(is_deleted=False, is_active=True).select_related("state"),
            "city_aliases": CityAlias.objects.filter(is_deleted=False, is_active=True).select_related("city", "city__state"),
            "groups": LocationGroup.objects.filter(is_deleted=False, is_active=True).select_related("city", "city__state"),
            "areas": Area.objects.filter(is_deleted=False, is_active=True).select_related("city", "city__state"),
            "area_aliases": AreaAlias.objects.filter(is_deleted=False, is_active=True).select_related("area", "area__city", "area__city__state"),
        }

    @staticmethod
    def _matches_normalized(candidate, normalized):
        candidate_norm = CRMLocationMatchEngine.normalize_text(candidate)
        return bool(candidate_norm and normalized and candidate_norm == normalized)

    @staticmethod
    def classify_message(text, raw_city="", channel=None):
        raw_text = str(text or "").strip()
        normalized = CRMLocationMatchEngine.normalize_text(raw_text)
        result = CRMLocationMatchEngine._base_result(raw_text)
        if not normalized:
            result.update(classification="greeting", reason="empty_message", should_request_location=True)
            return result

        normalized_greetings = {CRMLocationMatchEngine.normalize_text(item) for item in GREETING_WORDS}
        normalized_jobs = {CRMLocationMatchEngine.normalize_text(item) for item in JOB_INQUIRY_WORDS}
        normalized_services = {CRMLocationMatchEngine.normalize_text(item) for item in SERVICE_ACTION_WORDS}

        if normalized in normalized_jobs or any(word and word in normalized for word in normalized_jobs):
            result.update(classification="job_inquiry", confidence=0.95, reason="job_inquiry_phrase")
            return result
        if normalized in normalized_greetings:
            result.update(classification="greeting", confidence=0.95, reason="greeting_or_general", should_request_location=True)
            return result
        if normalized in normalized_services:
            result.update(classification="service_action", confidence=0.9, reason="service_action_phrase", raw_service=raw_text)
            return result

        # Branch labels often arrive as "SPA NAME - AREA". Match the branch and
        # then route through the real area part only.
        branch_part = raw_text
        area_part = ""
        if " - " in raw_text or "-" in raw_text:
            pieces = [part.strip() for part in re.split(r"\s+-\s+|-", raw_text, maxsplit=1) if part.strip()]
            if len(pieces) == 2:
                branch_part, area_part = pieces

        from apps.locations.services.fuzzy_matcher import (
            AUTO_APPLY_SCORE,
            SUGGESTION_SCORE,
            fuzzy_match_branch,
            fuzzy_match_location,
        )

        branch_match = None
        if area_part:
            branch_match = fuzzy_match_branch(
                branch_part,
                context={"raw_city": raw_city, "channel_id": getattr(channel, "id", None)},
            )
        else:
            branch_match = fuzzy_match_branch(
                raw_text,
                context={"raw_city": raw_city, "channel_id": getattr(channel, "id", None)},
            )
            # A plain area name may resemble a branch name. Only an explicit
            # "BRANCH - AREA" label or a high-confidence branch match may
            # pre-empt normal city/group/area matching.
            if branch_match and branch_match["score"] < AUTO_APPLY_SCORE:
                branch_match = None

        if branch_match:
            candidate = branch_match['candidate']
            score = branch_match['score']
            method = branch_match['method']
            branch = Branch.objects.filter(id=candidate['id'], is_active=True, is_deleted=False).first()
            if branch:
                branch_area_text = area_part or branch.area or branch.spa_name
                area_match = fuzzy_match_location(
                    branch_area_text,
                    context={"raw_city": raw_city or branch.city, "channel_id": getattr(channel, "id", None)},
                )
                area_score = area_match["score"] if area_part and area_match else score
                applied = score >= AUTO_APPLY_SCORE and area_score >= AUTO_APPLY_SCORE
                lead_area = None
                matched_area_name = branch_area_text
                if applied:
                    area_candidate = area_match["candidate"] if area_match else {}
                    if area_candidate.get("type") in ["area", "area_alias"]:
                        from apps.locations.models import Area

                        location_area = Area.objects.filter(
                            id=area_candidate.get("area_id") or area_candidate.get("id"),
                            is_active=True,
                            is_deleted=False,
                        ).first()
                        if location_area:
                            matched_area_name = location_area.name
                            lead_area = CRMLocationMatchEngine.ensure_area_from_location_area(location_area)
                    elif area_candidate.get("type") in ["doubletick_area", "doubletick_area_alias"]:
                        lead_area = DoubleTickLeadArea.objects.filter(
                            id=area_candidate.get("lead_area_id"),
                            is_active=True,
                            is_deleted=False,
                        ).first()
                        matched_area_name = area_candidate.get("area_name") or branch_area_text
                    if not lead_area:
                        lead_area = AreaMatchingService.ensure_area_from_branch(
                            branch_area_text, raw_city or branch.city, branch, channel
                        )
                result.update(
                    classification="branch",
                    confidence=min(score, area_score) / 100.0,
                    reason=f"branch_{method}_match",
                    branch=branch,
                    area=matched_area_name if applied else None,
                    raw_branch=branch.spa_name,
                    raw_city=(raw_city or branch.city) if applied else "",
                    raw_area=matched_area_name if applied else "",
                    matched_area=lead_area if applied else None,
                    current_branch=branch if applied else None,
                    should_request_location=not applied,
                    method=method
                )
                if SUGGESTION_SCORE <= min(score, area_score) < AUTO_APPLY_SCORE:
                    result['suggested_match'] = {
                        'name': branch.spa_name,
                        'type': 'branch',
                        'id': str(branch.id),
                        'area_name': matched_area_name,
                        'confidence': min(score, area_score) / 100.0,
                        'reason': f"Possible branch match: {branch.spa_name}"
                    }
                return result

        loc_match = fuzzy_match_location(
            raw_text,
            context={"raw_city": raw_city, "channel_id": getattr(channel, "id", None)},
        )
        if loc_match:
            candidate = loc_match['candidate']
            score = loc_match['score']
            method = loc_match['method']
            c_type = candidate['type']
            applied = score >= AUTO_APPLY_SCORE

            if c_type == 'state':
                result.update(
                    classification="state" if applied else "unknown",
                    confidence=score / 100.0,
                    reason=f"state_{method}",
                    raw_city="",
                    method=method
                )
                if not applied:
                    result["suggested_match"] = {
                        "name": candidate["name"], "type": "state", "id": str(candidate["id"]),
                        "confidence": score / 100.0, "reason": f"Possible state match: {candidate['name']}",
                    }
                return result

            elif c_type in ['city', 'city_alias']:
                from apps.locations.models import City
                city_id = candidate.get('city_id') or candidate['id']
                city = City.objects.filter(id=city_id, is_active=True, is_deleted=False).first()
                result.update(
                    classification="city" if applied else "unknown",
                    confidence=score / 100.0,
                    reason=f"city_{method}",
                    state=city.state if city else None,
                    city=city,
                    raw_city=city.name if city and applied else "",
                    raw_area="",
                    should_request_location=True,
                    method=method
                )
                if not applied and city:
                    result["suggested_match"] = {
                        "name": city.name, "type": "city", "id": str(city.id),
                        "confidence": score / 100.0, "reason": f"Possible city match: {city.name}",
                    }
                return result

            elif c_type == 'location_group':
                from apps.locations.models import LocationGroup
                group = LocationGroup.objects.filter(id=candidate['id'], is_active=True, is_deleted=False).first()
                result.update(
                    classification="location_group" if applied else "unknown",
                    confidence=score / 100.0,
                    reason=f"location_group_{method}",
                    state=group.city.state if group and group.city else None,
                    city=group.city if group else None,
                    location_group=group,
                    raw_city=group.city.name if group and group.city and applied else "",
                    raw_group=group.name if group and applied else "",
                    raw_area="",
                    should_request_location=True,
                    method=method
                )
                if not applied and group:
                    result["suggested_match"] = {
                        "name": group.name, "type": "location_group", "id": str(group.id),
                        "confidence": score / 100.0, "reason": f"Possible group match: {group.name}",
                    }
                return result

            elif c_type in ['area', 'area_alias']:
                from apps.locations.models import Area
                area_id = candidate.get('area_id') or candidate['id']
                area = Area.objects.filter(id=area_id, is_active=True, is_deleted=False).first()
                if area:
                    lead_area = (
                        CRMLocationMatchEngine.ensure_area_from_location_area(area)
                        if applied else None
                    )
                    result.update(
                        classification="area",
                        confidence=score / 100.0,
                        reason=f"area_{method}",
                        state=area.city.state if area.city else None,
                        city=area.city,
                        area=area,
                        raw_city=area.city.name if area.city and applied else "",
                        raw_area=area.name if applied else "",
                        matched_area=lead_area if applied else None,
                        should_request_location=not applied,
                        method=method
                    )
                    if SUGGESTION_SCORE <= score < AUTO_APPLY_SCORE:
                        result['suggested_match'] = {
                            'name': area.name,
                            'type': 'area',
                            'id': str(area.id),
                            'confidence': score / 100.0,
                            'reason': f"Fuzzy matched area '{area.name}' with score {score}"
                        }
                    return result

            elif c_type in ["doubletick_area", "doubletick_area_alias"]:
                lead_area = DoubleTickLeadArea.objects.filter(
                    id=candidate.get("lead_area_id"),
                    is_active=True,
                    is_deleted=False,
                ).first()
                if lead_area:
                    result.update(
                        classification="area",
                        confidence=score / 100.0,
                        reason=f"area_{method}",
                        raw_city=lead_area.city if applied else "",
                        raw_area=lead_area.name if applied else "",
                        matched_area=lead_area if applied else None,
                        should_request_location=not applied,
                        method=method,
                    )
                    if not applied:
                        result["suggested_match"] = {
                            "name": lead_area.name, "type": "lead_area", "id": str(lead_area.id),
                            "confidence": score / 100.0, "reason": f"Possible trained area match: {lead_area.name}",
                        }
                    return result

        result.update(classification="unknown", confidence=0.1, reason="no_location_match", should_request_location=True)
        return result


def send_lead_notification(lead, recipient):
    """
    Send FCM through the existing NotificationService.

    Only qualified/distributed leads call this; pending conversations never
    notify spa managers.
    """
    try:
        from apps.notifications.services import NotificationService
    except Exception as exc:
        return False, str(exc)

    name = lead.customer_name or lead.phone_number
    area = lead.matched_area.name if lead.matched_area else lead.raw_area
    service = lead.raw_service or lead.service_name or "WhatsApp inquiry"
    body = " - ".join(part for part in [name, area, service] if part)
    ok = NotificationService.send_push(
        recipient=recipient,
        title="New WhatsApp Lead",
        body=body,
        notification_type="doubletick_lead",
        data={
            "lead_id": str(lead.id),
            "source": "doubletick",
            "area": area or "",
            "service": service or "",
            "branch_id": str(lead.current_branch_id or lead.assigned_branch_id or ""),
        },
    )
    return ok, "" if ok else "Notification service returned failure."


class DoubleTickWebhookClassifier:
    """Small wrapper kept for tests and future provider-specific expansion."""

    @staticmethod
    def classify(payload):
        return classify_webhook_event(payload)


class PendingConversationService:
    """Business rules for incomplete customer conversations."""

    @staticmethod
    def is_greeting_only(text):
        normalized = normalize_area_text(text)
        return normalized in GREETING_WORDS

    @staticmethod
    def apply_pending_state(conversation, text):
        """
        Keep incomplete conversations out of spa-manager distribution.

        Greetings and vague intent messages are saved as conversation history,
        then held in the internal team queue until city/area is confirmed.
        """
        old_status = conversation.status
        if PendingConversationService.is_greeting_only(text):
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.GREETING_ONLY
        else:
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
        conversation.requires_manual_attention = True
        conversation.save(update_fields=["status", "pending_reason", "requires_manual_attention", "updated_at"])
        if old_status != conversation.status:
            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                old_status=old_status,
                new_status=conversation.status,
                note=conversation.pending_reason,
            )
        return conversation

    @staticmethod
    def mark_stale_conversations(now=None):
        """Move old pending conversations to the manual-attention queue."""
        now = now or timezone.now()
        minutes = int(getattr(settings, "DOUBLETICK_PENDING_ATTENTION_MINUTES", 10))
        cutoff = now - timedelta(minutes=minutes)
        queryset = DoubleTickConversation.objects.filter(
            status__in=[
                DoubleTickConversation.Status.AWAITING_LOCATION,
                DoubleTickConversation.Status.AWAITING_CUSTOMER,
                DoubleTickConversation.Status.PENDING,
            ],
            requires_manual_attention=False,
            last_customer_message_at__lt=cutoff,
        )
        updated = 0
        for conversation in queryset:
            old_status = conversation.status
            conversation.status = DoubleTickConversation.Status.MANUAL_ATTENTION
            conversation.pending_reason = DoubleTickConversation.PendingReason.CUSTOMER_STOPPED_REPLYING
            conversation.requires_manual_attention = True
            conversation.save(update_fields=["status", "pending_reason", "requires_manual_attention", "updated_at"])
            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.MANUAL_ATTENTION_REQUIRED,
                old_status=old_status,
                new_status=conversation.status,
                note="Customer stopped replying.",
            )
            updated += 1
        return updated


class GreetingAutomationService:
    """Save first-touch bot messages and send them when DoubleTick API is configured."""

    @staticmethod
    def _create_outbound(conversation, text, message_type="text", origin=None, interactive_payload=None):
        now = timezone.now()
        fingerprint = "|".join([str(conversation.id), message_type, text, now.isoformat()])
        dt_message_id = "local-" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
        message = DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=conversation.current_lead,
            customer=conversation.customer,
            dt_message_id=dt_message_id,
            message_id=dt_message_id,
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin=origin or DoubleTickMessage.Origin.BOT,
            message_type=message_type,
            text=text,
            interactive_payload=interactive_payload or {},
            status=DoubleTickMessage.Status.QUEUED,
            sender_display_name="Bot",
            customer_number=conversation.customer.phone_number,
            waba_number=conversation.channel.waba_number if conversation.channel else "",
            message_timestamp=now,
            sent_at=now,
            raw_payload={"local_automation": True},
        )
        return message

    @staticmethod
    def send_first_touch(conversation):
        if conversation.messages.filter(direction=DoubleTickMessage.Direction.OUTBOUND, origin=DoubleTickMessage.Origin.BOT).exists():
            return []
        greeting_text = getattr(
            settings,
            "DOUBLETICK_GREETING_MESSAGE",
            "Namaste! Thanks for messaging us. Please choose your nearest location so we can connect you with the right spa.",
        )
        list_text = getattr(settings, "DOUBLETICK_LOCATION_REQUEST_MESSAGE", LOCATION_REQUEST_MESSAGE)
        messages = [
            GreetingAutomationService._create_outbound(conversation, greeting_text, "text"),
            GreetingAutomationService._create_outbound(
                conversation,
                list_text,
                "interactive_list",
                interactive_payload={"purpose": "location_request"},
            ),
        ]
        for message in messages:
            if not getattr(settings, "DOUBLETICK_API_KEY", ""):
                message.status = DoubleTickMessage.Status.QUEUED
                message.failure_reason = "DoubleTick API key is not configured; message saved locally."
                message.save(update_fields=["status", "failure_reason", "updated_at"])
                continue
            try:
                response = DoubleTickReplyService._send_text(conversation, message.text)
                message.status = DoubleTickMessage.Status.SENT
                message.raw_payload = response
                message.save(update_fields=["status", "raw_payload", "updated_at"])
            except Exception as exc:
                message.status = DoubleTickMessage.Status.FAILED
                message.failed_at = timezone.now()
                message.failure_reason = str(exc)
                message.save(update_fields=["status", "failed_at", "failure_reason", "updated_at"])
        conversation.last_agent_message_at = timezone.now()
        conversation.team_last_replied_at = conversation.last_agent_message_at
        conversation.save(update_fields=["last_agent_message_at", "team_last_replied_at", "updated_at"])
        _activity(conversation=conversation, action=DoubleTickActivity.Action.LOCATION_REQUESTED)
        return messages


class AutoLocationRequestService:
    """Send one location request for vague inbound customer messages."""

    @staticmethod
    def recently_requested(conversation, now=None):
        now = now or timezone.now()
        cutoff = now - timedelta(minutes=30)
        return conversation.messages.filter(
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin__in=[DoubleTickMessage.Origin.BOT, DoubleTickMessage.Origin.API],
            text=LOCATION_REQUEST_MESSAGE,
            created_at__gte=cutoff,
        ).exists()

    @staticmethod
    def request_if_needed(conversation, match_result, now=None):
        if not getattr(settings, "DOUBLETICK_AUTO_REPLY_ENABLED", False):
            return None
        now = now or timezone.now()
        if not match_result.get("should_request_location"):
            return None
        if match_result.get("classification") == "job_inquiry":
            return None
        if conversation.matched_area_id or conversation.raw_area:
            return None
        if AutoLocationRequestService.recently_requested(conversation, now):
            return None

        fingerprint = "|".join([str(conversation.id), "location-request", now.isoformat()])
        dt_message_id = "local-" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
        message = DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=conversation.current_lead,
            customer=conversation.customer,
            dt_message_id=dt_message_id,
            message_id=dt_message_id,
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin=DoubleTickMessage.Origin.BOT,
            message_type="text",
            text=LOCATION_REQUEST_MESSAGE,
            status=DoubleTickMessage.Status.QUEUED,
            sender_display_name="Bot",
            customer_number=conversation.customer.phone_number,
            waba_number=conversation.channel.waba_number if conversation.channel else "",
            message_timestamp=now,
            sent_at=now,
            raw_payload={"local_automation": True, "purpose": "location_request"},
        )
        if getattr(settings, "DOUBLETICK_API_KEY", ""):
            try:
                response = DoubleTickReplyService._send_text(conversation, LOCATION_REQUEST_MESSAGE)
                message.status = DoubleTickMessage.Status.SENT
                message.raw_payload = response
                message.save(update_fields=["status", "raw_payload", "updated_at"])
            except Exception as exc:
                message.status = DoubleTickMessage.Status.FAILED
                message.failed_at = timezone.now()
                message.failure_reason = str(exc)
                message.save(update_fields=["status", "failed_at", "failure_reason", "updated_at"])

        conversation.last_agent_message_at = now
        conversation.team_last_replied_at = now
        conversation.save(update_fields=["last_agent_message_at", "team_last_replied_at", "updated_at"])
        _activity(
            conversation=conversation,
            lead=conversation.current_lead,
            action=DoubleTickActivity.Action.LOCATION_REQUESTED,
            note="Auto location request sent.",
            metadata={"classification": match_result.get("classification"), "reason": match_result.get("reason")},
        )
        return message


class AreaMatchingService:
    """Controlled area and alias matching."""

    @staticmethod
    def _find_or_create_lead_area_from_crm(raw_area, raw_city="", channel=None):
        location_area = CRMLocationMatchEngine.find_area(raw_area, raw_city)
        if not location_area:
            return None
        return CRMLocationMatchEngine.ensure_area_from_location_area(location_area, raw_alias=raw_area, channel=channel)

    @staticmethod
    def find_area(raw_area, raw_city="", channel=None, create_if_missing=True):
        normalized = normalize_area_text(raw_area)
        if not normalized:
            return None

        alias_qs = DoubleTickAreaAlias.objects.select_related("lead_area").filter(
            normalized_alias=normalized,
            is_active=True,
            lead_area__is_active=True,
        )
        if channel:
            alias_qs = alias_qs.filter(Q(channel=channel) | Q(channel__isnull=True))
        alias = alias_qs.order_by("-channel_id").first()
        if alias:
            return alias.lead_area

        area_qs = DoubleTickLeadArea.objects.filter(normalized_name=normalized, is_active=True)
        if raw_city:
            area_qs = area_qs.filter(Q(city__iexact=raw_city) | Q(city=""))
        lead_area = area_qs.order_by("priority", "name").first()
        if lead_area:
            return lead_area

        if create_if_missing:
            return AreaMatchingService._find_or_create_lead_area_from_crm(raw_area, raw_city, channel)
        return None

    @staticmethod
    def find_branch_candidates(raw_area, raw_city=""):
        """
        Find active spa branches using normalized CRM location FK coverage first,
        then fall back to legacy branch city/area/spa text matching.

        Priority:
          1. Branch.location_area PK match via CRM Area
          2. BranchCoverageArea CRM coverage mapping
          3. Legacy text-field fuzzy match (backward-compat fallback)
        """
        normalized_area = normalize_area_text(raw_area)
        normalized_city = normalize_area_text(raw_city)
        if not normalized_area and not normalized_city:
            return []

        try:
            from django.contrib.contenttypes.models import ContentType
            from apps.locations.models import BranchCoverageArea

            location_area = CRMLocationMatchEngine.find_area(raw_area, raw_city)
            if location_area:
                fk_branches = list(
                    Branch.objects.filter(
                        is_active=True,
                        is_deleted=False,
                        location_area=location_area,
                    ).order_by("spa_name")
                )
                if fk_branches:
                    return fk_branches

                branch_ct = ContentType.objects.get_for_model(Branch)
                coverage_qs = BranchCoverageArea.objects.filter(
                    is_deleted=False,
                    is_active=True,
                    area=location_area,
                    content_type=branch_ct,
                ).order_by("priority", "-is_primary")
                pk_branch_ids = list(coverage_qs.values_list("object_id", flat=True))
                if pk_branch_ids:
                    pk_branches = list(
                        Branch.objects.filter(
                            id__in=pk_branch_ids,
                            is_active=True,
                            is_deleted=False,
                        ).order_by("spa_name")
                    )
                    if pk_branches:
                        return pk_branches
        except Exception:
            pass

        branches = Branch.objects.filter(is_active=True, is_deleted=False)
        if normalized_city:
            branches = branches.filter(city__iexact=raw_city)

        matches = []
        for branch in branches:
            score = 0
            if normalized_area:
                if normalize_area_text(branch.area) == normalized_area:
                    score += 100
                elif _contains_normalized(branch.area, raw_area):
                    score += 80
                elif _contains_normalized(branch.spa_name, raw_area):
                    score += 60
                elif _contains_normalized(branch.address, raw_area):
                    score += 45
            if normalized_city and normalize_area_text(branch.city) == normalized_city:
                score += 20
            if score > 0:
                matches.append((score, branch))

        matches.sort(key=lambda item: (-item[0], item[1].spa_name or ""))
        return [branch for _, branch in matches]


    @staticmethod
    def ensure_area_from_branch(raw_area, raw_city="", branch=None, channel=None):
        """
        Create or reuse a DoubleTickLeadArea from branch metadata and map it to
        the branch. This lets leads route even before an admin has manually
        created the DoubleTick area screen entry.
        """
        raw_area = str(raw_area or "").strip()
        raw_city = str(raw_city or "").strip()
        if not raw_area and branch:
            raw_area = branch.area or branch.spa_name
        if not raw_city and branch:
            raw_city = branch.city
        normalized = normalize_area_text(raw_area)
        if not normalized:
            return None

        lead_area = AreaMatchingService.find_area(raw_area, raw_city, channel)
        if not lead_area:
            lead_area, _ = DoubleTickLeadArea.objects.get_or_create(
                normalized_name=normalized,
                city=raw_city or "",
                defaults={
                    "name": raw_area,
                    "state": getattr(branch, "state", "") if branch else "",
                    "is_active": True,
                    "description": "Auto-created from existing spa branch location during DoubleTick matching.",
                },
            )

        if raw_area:
            DoubleTickAreaAlias.objects.get_or_create(
                lead_area=lead_area,
                normalized_alias=normalized,
                defaults={
                    "alias": raw_area,
                    "channel": channel,
                    "created_from_manual_mapping": True,
                },
            )

        if branch:
            DoubleTickLeadAreaBranch.objects.get_or_create(
                lead_area=lead_area,
                branch=branch,
                defaults={
                    "is_active": True,
                    "receives_leads": True,
                    "notes": "Auto-created from branch city/area/spa metadata.",
                },
            )
        return lead_area

    @staticmethod
    def apply_match_result(conversation, match_result):
        metadata = dict(conversation.raw_payload or {})
        if "suggested_match" in match_result:
            metadata["suggested_match"] = match_result["suggested_match"]
        else:
            metadata.pop("suggested_match", None)

        metadata["location_match"] = {
            key: (
                str(value.id) if hasattr(value, "id") else value
            )
            for key, value in match_result.items()
            if key not in {"state", "city", "location_group", "area", "branch", "matched_area", "current_branch", "suggested_match"}
        }
        conversation.raw_payload = metadata

        classification = match_result.get("classification")
        if classification == "city":
            conversation.raw_city = match_result.get("raw_city") or ""
            conversation.raw_area = ""
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
            conversation.requires_manual_attention = True
            conversation.area_confirmed = False
            conversation.matched_area = None
        elif classification == "location_group":
            conversation.raw_city = match_result.get("raw_city") or conversation.raw_city
            conversation.raw_area = ""
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
            conversation.requires_manual_attention = True
            conversation.area_confirmed = False
            conversation.matched_area = None
        elif classification in ["area", "branch"]:
            if match_result.get("matched_area"):
                conversation.raw_city = match_result.get("raw_city") or conversation.raw_city
                conversation.raw_area = match_result.get("raw_area") or ""
                conversation.matched_area = match_result["matched_area"]
                conversation.area_confirmed = True
                conversation.status = DoubleTickConversation.Status.QUALIFIED
                conversation.pending_reason = ""
                conversation.requires_manual_attention = False
            else:
                conversation.raw_city = match_result.get("raw_city") or conversation.raw_city
                conversation.raw_area = match_result.get("raw_area") or ""
                conversation.status = DoubleTickConversation.Status.AREA_UNMATCHED
                conversation.pending_reason = DoubleTickConversation.PendingReason.UNMATCHED_LOCATION
                conversation.requires_manual_attention = True
                conversation.area_confirmed = False
                conversation.matched_area = None
        elif classification == "service_action":
            conversation.raw_service = match_result.get("raw_service") or conversation.raw_service
            conversation.raw_area = ""
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
            conversation.requires_manual_attention = True
            conversation.area_confirmed = False
        elif classification == "job_inquiry":
            conversation.raw_area = ""
            conversation.status = DoubleTickConversation.Status.MANUAL_ATTENTION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MANUAL_REPLY_REQUIRED
            conversation.requires_manual_attention = True
            conversation.area_confirmed = False
            conversation.matched_area = None
        elif classification in ["greeting", "unknown", "state"]:
            conversation.raw_area = ""
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = (
                DoubleTickConversation.PendingReason.GREETING_ONLY
                if classification == "greeting"
                else DoubleTickConversation.PendingReason.MISSING_LOCATION
            )
            conversation.requires_manual_attention = True
            conversation.area_confirmed = False
            conversation.matched_area = None

        conversation.save()

        raw_text = match_result.get("input") or ""
        normalized = CRMLocationMatchEngine.normalize_text(raw_text)
        method = match_result.get("method") or ("exact" if match_result.get("confidence", 0) == 1.0 else "none")

        _activity(
            conversation=conversation,
            action=(
                DoubleTickActivity.Action.AREA_MATCHED
                if conversation.matched_area_id
                else DoubleTickActivity.Action.AREA_UNMATCHED
            ),
            new_status=conversation.status,
            note=match_result.get("reason", ""),
            metadata={
                "original_text": raw_text,
                "normalized_text": normalized,
                "method": method,
                "classification": classification,
                "confidence": match_result.get("confidence", 0.0),
                "reason": match_result.get("reason", ""),
                "applied": "yes" if conversation.area_confirmed else "no",
                "matched_city": match_result.get("raw_city") or "",
                "matched_group": match_result.get("raw_group") or "",
                "matched_area": getattr(conversation.matched_area, "name", "") if conversation.matched_area else "",
                "matched_branch": getattr(match_result.get("branch"), "spa_name", "") if match_result.get("branch") else "",
                "conversation_id": str(conversation.id),
                "lead_id": str(conversation.current_lead_id) if conversation.current_lead_id else "",
            },
        )
        return conversation

    @staticmethod
    def match_conversation(conversation, raw_area=None, raw_city=None, save_alias=False):
        raw_area = raw_area if raw_area is not None else conversation.raw_area
        raw_city = raw_city if raw_city is not None else conversation.raw_city
        lead_area = AreaMatchingService.find_area(raw_area, raw_city, conversation.channel)
        auto_matched_branch = None
        if not lead_area and getattr(settings, "DOUBLETICK_AUTO_CREATE_AREA_FROM_BRANCH", True):
            branch_candidates = AreaMatchingService.find_branch_candidates(raw_area, raw_city)
            if branch_candidates:
                auto_matched_branch = branch_candidates[0]
                lead_area = AreaMatchingService.ensure_area_from_branch(raw_area, raw_city, auto_matched_branch, conversation.channel)
        if not lead_area:
            old_status = conversation.status
            conversation.status = DoubleTickConversation.Status.AREA_UNMATCHED
            conversation.pending_reason = DoubleTickConversation.PendingReason.UNMATCHED_LOCATION
            conversation.requires_manual_attention = True
            conversation.save(update_fields=["status", "pending_reason", "requires_manual_attention", "updated_at"])
            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.AREA_UNMATCHED,
                old_status=old_status,
                new_status=conversation.status,
                note=raw_area or "",
                metadata={"raw_city": raw_city or "", "raw_area": raw_area or ""},
            )
            return None

        conversation.matched_area = lead_area
        conversation.area_confirmed = True
        conversation.status = DoubleTickConversation.Status.QUALIFIED
        conversation.pending_reason = ""
        conversation.requires_manual_attention = False
        conversation.save(update_fields=[
            "matched_area",
            "area_confirmed",
            "status",
            "pending_reason",
            "requires_manual_attention",
            "updated_at",
        ])
        if save_alias and raw_area:
            DoubleTickAreaAlias.objects.get_or_create(
                lead_area=lead_area,
                normalized_alias=normalize_area_text(raw_area),
                defaults={
                    "alias": raw_area,
                    "channel": conversation.channel,
                    "created_from_manual_mapping": True,
                },
            )
        _activity(
            conversation=conversation,
            action=DoubleTickActivity.Action.AREA_MATCHED,
            new_status=conversation.status,
            metadata={
                "lead_area_id": str(lead_area.id),
                "auto_matched_branch_id": str(auto_matched_branch.id) if auto_matched_branch else "",
                "raw_city": raw_city or "",
                "raw_area": raw_area or "",
            },
        )
        return lead_area


class DoubleTickConversationService:
    """Create/update customers, conversations and messages from webhooks."""

    @staticmethod
    def _choose_customer(queryset, reason):
        customers = list(queryset.order_by("created_at")[:50])
        if not customers:
            return None, 0

        count = queryset.count()
        customer = sorted(
            customers,
            key=lambda item: (
                -sum(
                    1
                    for value in [
                        item.customer_name,
                        item.whatsapp_name,
                        item.dt_customer_id,
                        item.normalized_phone,
                        item.phone_number,
                        item.channel_id,
                    ]
                    if value
                ),
                item.created_at,
            ),
        )[0]
        if count > 1:
            logger.warning(
                "DoubleTickCustomer duplicate group resolved without crashing webhook: reason=%s canonical_id=%s duplicate_count=%s",
                reason,
                customer.id,
                count,
            )
        return customer, count

    @staticmethod
    def _upsert_customer(parsed, payload, channel=None):
        now = timezone.now()
        dt_customer_id = parsed.get("doubletick_customer_id") or first_value(payload, ["dt_customer_id", "customer.id", "customerId"])
        normalized_phone = parsed.get("normalized_phone") or normalize_phone(parsed.get("phone_number"))
        if not normalized_phone and not dt_customer_id:
            raise ValidationError("Webhook payload does not contain a customer id or phone number.")

        customer = None
        created = False

        if dt_customer_id and channel:
            customer, _ = DoubleTickConversationService._choose_customer(
                DoubleTickCustomer.objects.filter(dt_customer_id=dt_customer_id, channel=channel),
                "dt_customer_id_channel",
            )
        if not customer and normalized_phone and channel:
            customer, _ = DoubleTickConversationService._choose_customer(
                DoubleTickCustomer.objects.filter(normalized_phone=normalized_phone, channel=channel),
                "normalized_phone_channel",
            )
        if not customer and dt_customer_id and not channel:
            customer, _ = DoubleTickConversationService._choose_customer(
                DoubleTickCustomer.objects.filter(dt_customer_id=dt_customer_id, channel__isnull=True),
                "dt_customer_id_no_channel",
            )
        if not customer and normalized_phone:
            phone_matches = DoubleTickCustomer.objects.filter(normalized_phone=normalized_phone)
            if channel:
                phone_matches = phone_matches.filter(Q(channel=channel) | Q(channel__isnull=True))
            customer, _ = DoubleTickConversationService._choose_customer(
                phone_matches,
                "normalized_phone_safe",
            )

        if not customer:
            customer = DoubleTickCustomer.objects.create(
                dt_customer_id=dt_customer_id or "",
                phone_number=parsed.get("phone_number", ""),
                normalized_phone=normalized_phone or "",
                customer_name=parsed.get("customer_name", ""),
                whatsapp_name=parsed.get("whatsapp_name", ""),
                channel=channel,
                raw_profile=payload.get("customer", {}) if isinstance(payload, dict) else {},
                first_seen_at=now,
                last_seen_at=now,
            )
            created = True

        updates = []
        for field, value in {
            "dt_customer_id": dt_customer_id or customer.dt_customer_id,
            "phone_number": parsed.get("phone_number", ""),
            "normalized_phone": normalized_phone,
            "customer_name": parsed.get("customer_name", ""),
            "whatsapp_name": parsed.get("whatsapp_name", ""),
            "channel": channel or customer.channel,
            "raw_profile": payload.get("customer", {}) if isinstance(payload, dict) else {},
            "last_seen_at": now,
        }.items():
            if value and getattr(customer, field) != value:
                setattr(customer, field, value)
                updates.append(field)
        if not customer.first_seen_at:
            customer.first_seen_at = now
            updates.append("first_seen_at")
        if updates:
            customer.save(update_fields=updates + ["updated_at"])
        return customer, created

    @staticmethod
    def _get_or_create_conversation(customer, parsed, payload, channel=None):
        now = timezone.now()
        dt_conversation_id = parsed.get("doubletick_chat_id") or first_value(payload, ["chat.id", "chatId", "conversation.id"])
        conversation = None
        if dt_conversation_id:
            conversation = DoubleTickConversation.objects.filter(dt_conversation_id=dt_conversation_id).first()
        if not conversation:
            conversation = DoubleTickConversation.objects.filter(
                customer=customer,
                status__in=[
                    DoubleTickConversation.Status.NEW,
                    DoubleTickConversation.Status.PENDING,
                    DoubleTickConversation.Status.AWAITING_LOCATION,
                    DoubleTickConversation.Status.AWAITING_CUSTOMER,
                    DoubleTickConversation.Status.AREA_UNMATCHED,
                    DoubleTickConversation.Status.MANUAL_ATTENTION,
                    DoubleTickConversation.Status.QUALIFIED,
                    DoubleTickConversation.Status.DISTRIBUTED,
                ],
            ).order_by("-last_message_at", "-created_at").first()
        created = False
        if not conversation:
            conversation = DoubleTickConversation.objects.create(
                customer=customer,
                channel=channel,
                status=DoubleTickConversation.Status.NEW,
                dt_conversation_id=str(dt_conversation_id or ""),
                raw_payload=payload,
            )
            created = True
            _activity(conversation=conversation, action=DoubleTickActivity.Action.CONVERSATION_CREATED)
        elif channel and not conversation.channel_id:
            conversation.channel = channel
            conversation.save(update_fields=["channel", "updated_at"])
        return conversation, created

    @staticmethod
    def upsert_inbound_message(payload):
        parsed = parse_doubletick_payload(payload)
        channel = find_channel_from_payload(payload)
        customer, _ = DoubleTickConversationService._upsert_customer(parsed, payload, channel)
        conversation, _ = DoubleTickConversationService._get_or_create_conversation(customer, parsed, payload, channel)

        received_at = _timestamp_from_payload(payload)
        dt_message_id = parsed.get("doubletick_message_id") or first_value(payload, ["dtMessageId", "message.id", "messageId"])
        text = parsed.get("message", "") or _message_text(payload)
        message_type = _provider_message_type(payload)
        interactive_payload = first_value(payload, [
            "interactive",
            "message.interactive",
            "button",
            "listReply",
            "reply",
            "flowResponse",
            "flow_response",
            "data.interactive",
        ], default={}) or {}
        if not dt_message_id:
            fingerprint = "|".join([
                str(conversation.id),
                customer.normalized_phone or "",
                received_at.isoformat(),
                text,
            ])
            dt_message_id = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
        message, created = DoubleTickMessage.objects.get_or_create(
            dt_message_id=str(dt_message_id or ""),
            conversation=conversation,
            defaults={
                "message_id": str(first_value(payload, ["messageId", "message.id"]) or dt_message_id or ""),
                "lead": conversation.current_lead,
                "customer": customer,
                "direction": DoubleTickMessage.Direction.INBOUND,
                "origin": DoubleTickMessage.Origin.CUSTOMER,
                "message_type": message_type,
                "text": text,
                "interactive_payload": interactive_payload if isinstance(interactive_payload, dict) else {"value": interactive_payload},
                "status": DoubleTickMessage.Status.RECEIVED,
                "customer_number": parsed.get("phone_number", ""),
                "waba_number": normalize_waba_number(first_value(payload, [
                    "waba_number",
                    "wabaNumber",
                    "channel.waba_number",
                    "data.wabaNumber",
                    "data.channel.waba_number",
                    "to",
                    "from",
                ])),
                "message_timestamp": received_at,
                "received_at": received_at,
                "raw_payload": payload,
            },
        )
        if not created:
            return conversation, message, False

        conversation.first_message_at = conversation.first_message_at or received_at
        conversation.last_message_at = received_at
        conversation.last_customer_message_at = received_at
        conversation.customer_last_replied_at = received_at
        conversation.unread_count += 1
        conversation.raw_payload = payload

        extracted_city = parsed.get("city")
        extracted_area = parsed.get("area")
        extracted_service = parsed.get("service_name")
        if extracted_city:
            conversation.raw_city = extracted_city
        if extracted_area:
            conversation.raw_area = extracted_area
        if extracted_service:
            conversation.raw_service = extracted_service

        conversation.save()
        _activity(conversation=conversation, action=DoubleTickActivity.Action.MESSAGE_RECEIVED, metadata={"message_id": str(message.id)})
        return conversation, message, True

    @staticmethod
    def update_outbound_status(payload):
        provider_status = first_value(payload, ["status", "message.status", "data.status", "eventType", "event"])
        message_id = str(first_value(payload, ["messageId", "message.id", "dtMessageId", "data.messageId"]) or "")
        if not message_id:
            return None

        status_timestamp = _timestamp_from_payload(payload)
        existing_message = DoubleTickMessage.objects.filter(
            Q(message_id=message_id) | Q(dt_message_id=message_id)
        ).select_related("conversation", "lead", "customer").first()
        if existing_message:
            old_status = existing_message.status
            new_status = _status_to_message_status(provider_status)
            existing_message.status = new_status
            if new_status == DoubleTickMessage.Status.SENT:
                existing_message.sent_at = existing_message.sent_at or status_timestamp
            elif new_status == DoubleTickMessage.Status.DELIVERED:
                existing_message.delivered_at = existing_message.delivered_at or status_timestamp
            elif new_status == DoubleTickMessage.Status.READ:
                existing_message.read_at = existing_message.read_at or status_timestamp
            elif new_status == DoubleTickMessage.Status.FAILED:
                existing_message.failed_at = existing_message.failed_at or status_timestamp
                existing_message.failure_reason = str(first_value(payload, ["reason", "error", "failure_reason"]) or "")
            existing_message.raw_payload = payload
            existing_message.save(update_fields=[
                "status",
                "sent_at",
                "delivered_at",
                "read_at",
                "failed_at",
                "failure_reason",
                "raw_payload",
                "updated_at",
            ])
            _activity(
                conversation=existing_message.conversation,
                lead=existing_message.lead,
                action=DoubleTickActivity.Action.PROCESSING_FAILED if existing_message.status == DoubleTickMessage.Status.FAILED else DoubleTickActivity.Action.MESSAGE_SENT,
                old_status=old_status,
                new_status=existing_message.status,
                metadata={"message_id": str(existing_message.id), "provider_message_id": message_id, "status": existing_message.status},
            )
            return existing_message

        customer_number = str(first_value(payload, ["to", "customer.phone", "customer.phone_number"]) or "")
        waba_number = str(first_value(payload, ["wabaNumber", "waba_number", "channel.waba_number", "from"]) or "")
        sent_by_raw = str(first_value(payload, ["sentBy", "sent_by", "data.sentBy"]) or "")
        assigned_to_raw = str(first_value(payload, ["assignedTo", "assigned_to", "data.assignedTo"]) or "")
        dt_customer_id = str(first_value(payload, ["dtCustomerId", "dt_customer_id", "customer.id", "customerId"]) or "")
        channel = _channel_from_waba_number(waba_number)
        normalized_customer = normalize_phone(customer_number)

        customer = None
        if dt_customer_id:
            customer = DoubleTickCustomer.objects.filter(dt_customer_id=dt_customer_id).first()
        if not customer and normalized_customer:
            customer = DoubleTickCustomer.objects.filter(normalized_phone=normalized_customer).first()
        if not customer:
            parsed = {
                "doubletick_customer_id": dt_customer_id,
                "phone_number": customer_number,
                "normalized_phone": normalized_customer,
                "customer_name": str(first_value(payload, ["customerName", "customer.name", "contact.name"]) or ""),
                "whatsapp_name": "",
            }
            customer, _ = DoubleTickConversationService._upsert_customer(parsed, payload, channel)

        conversation = None
        if dt_customer_id:
            conversation = DoubleTickConversation.objects.filter(customer__dt_customer_id=dt_customer_id).order_by("-last_message_at", "-created_at").first()
        if not conversation and normalized_customer:
            conversation_qs = DoubleTickConversation.objects.filter(customer__normalized_phone=normalized_customer)
            if channel:
                conversation_qs = conversation_qs.filter(Q(channel=channel) | Q(channel__isnull=True))
            conversation = conversation_qs.order_by("-last_message_at", "-created_at").first()
        if not conversation:
            parsed = {"doubletick_chat_id": "", "doubletick_customer_id": dt_customer_id}
            conversation, _ = DoubleTickConversationService._get_or_create_conversation(customer, parsed, payload, channel)

        origin, sender_display_name, crm_user = _resolve_outbound_sender(sent_by_raw, assigned_to_raw, channel)
        message = DoubleTickMessage.objects.filter(
            Q(message_id=message_id) | Q(dt_message_id=message_id),
            direction=DoubleTickMessage.Direction.OUTBOUND,
        ).first()
        if not message:
            message = DoubleTickMessage.objects.create(
                conversation=conversation,
                lead=conversation.current_lead,
                customer=customer,
                dt_message_id=message_id,
                message_id=message_id,
                direction=DoubleTickMessage.Direction.OUTBOUND,
                origin=origin,
                sender_display_name=sender_display_name,
                sent_by=crm_user,
                sent_by_raw=sent_by_raw,
                assigned_to_raw=assigned_to_raw,
                message_type=_provider_message_type(payload),
                text=_message_text(payload),
                customer_number=customer_number,
                waba_number=waba_number,
                message_timestamp=status_timestamp,
                raw_payload=payload,
            )

        old_status = message.status
        new_status = _status_to_message_status(provider_status)
        status_rank = {
            DoubleTickMessage.Status.QUEUED: 0,
            DoubleTickMessage.Status.SENT: 1,
            DoubleTickMessage.Status.DELIVERED: 2,
            DoubleTickMessage.Status.READ: 3,
            DoubleTickMessage.Status.FAILED: 4,
        }
        if status_rank.get(new_status, 0) >= status_rank.get(message.status, 0):
            message.status = new_status
        if new_status == DoubleTickMessage.Status.SENT:
            message.sent_at = message.sent_at or status_timestamp
        elif new_status == DoubleTickMessage.Status.DELIVERED:
            message.delivered_at = message.delivered_at or status_timestamp
        elif new_status == DoubleTickMessage.Status.READ:
            message.read_at = message.read_at or status_timestamp
        elif new_status == DoubleTickMessage.Status.FAILED:
            message.failed_at = message.failed_at or status_timestamp
            message.failure_reason = str(first_value(payload, ["reason", "error", "failure_reason"]) or "")
        if not message.text:
            message.text = _message_text(payload)
        if not message.sender_display_name:
            message.sender_display_name = sender_display_name
        if not message.sent_by_id and crm_user:
            message.sent_by = crm_user
        message.origin = message.origin or origin
        message.customer = message.customer or customer
        message.lead = message.lead or conversation.current_lead
        message.customer_number = message.customer_number or customer_number
        message.waba_number = message.waba_number or waba_number
        message.message_timestamp = message.message_timestamp or status_timestamp
        message.sent_by_raw = message.sent_by_raw or sent_by_raw
        message.assigned_to_raw = message.assigned_to_raw or assigned_to_raw
        message.raw_payload = payload
        message.save()

        conversation.last_message_at = max(filter(None, [conversation.last_message_at, message.message_timestamp, status_timestamp]), default=status_timestamp)
        conversation.last_agent_message_at = max(filter(None, [conversation.last_agent_message_at, status_timestamp]), default=status_timestamp)
        conversation.team_last_replied_at = max(filter(None, [conversation.team_last_replied_at, status_timestamp]), default=status_timestamp)
        conversation.raw_payload = payload
        conversation.save(update_fields=["last_message_at", "last_agent_message_at", "team_last_replied_at", "raw_payload", "updated_at"])
        _activity(
            conversation=message.conversation,
            lead=message.lead,
            action=DoubleTickActivity.Action.MESSAGE_SENT if message.status != DoubleTickMessage.Status.FAILED else DoubleTickActivity.Action.PROCESSING_FAILED,
            old_status=old_status,
            new_status=message.status,
            metadata={"message_id": str(message.id), "provider_message_id": message_id, "status": message.status},
        )
        return message


class LeadQualificationService:
    """Convert confirmed conversations into qualified area leads."""

    TERMINAL_LEAD_STATUSES = {
        DoubleTickLead.Status.BOOKED,
        DoubleTickLead.Status.NOT_INTERESTED,
        DoubleTickLead.Status.LOST,
        DoubleTickLead.Status.CLOSED,
        DoubleTickLead.Status.EXPIRED,
    }

    @staticmethod
    @transaction.atomic
    def ensure_conversation_lead(conversation, user=None, matched_area=None, distribute=True):
        now = timezone.now()
        lead = conversation.current_lead
        if lead and lead.status in LeadQualificationService.TERMINAL_LEAD_STATUSES:
            lead = None
        first_message = conversation.messages.order_by("received_at", "created_at").first()
        latest_customer = conversation.messages.filter(direction=DoubleTickMessage.Direction.INBOUND).order_by("-received_at", "-created_at").first()
        area = matched_area or conversation.matched_area
        has_area = bool(conversation.area_confirmed and area)
        lead_status = DoubleTickLead.Status.QUALIFIED if has_area else DoubleTickLead.Status.UNASSIGNED
        defaults = {
            "customer": conversation.customer,
            "channel": conversation.channel,
            "customer_name": conversation.customer.customer_name,
            "phone_number": conversation.customer.phone_number,
            "normalized_phone": conversation.customer.normalized_phone,
            "initial_message": first_message.text if first_message else "",
            "latest_customer_message": latest_customer.text if latest_customer else "",
            "message": latest_customer.text if latest_customer else "",
            "raw_city": conversation.raw_city,
            "raw_area": conversation.raw_area,
            "raw_service": conversation.raw_service,
            "city": conversation.raw_city,
            "area": conversation.raw_area if has_area else "",
            "service_name": conversation.raw_service,
            "matched_area": area if has_area else None,
            "status": lead_status,
            "dt_customer_id": conversation.customer.dt_customer_id,
            "doubletick_customer_id": conversation.customer.dt_customer_id,
            "dt_first_message_id": first_message.dt_message_id if first_message else "",
            "dt_last_message_id": latest_customer.dt_message_id if latest_customer else "",
            "doubletick_message_id": latest_customer.dt_message_id if latest_customer else "",
            "received_at": conversation.first_message_at,
            "qualified_at": now if has_area else None,
            "area_matched_at": now if has_area else None,
            "raw_payload": conversation.raw_payload,
        }
        if lead:
            for field, value in defaults.items():
                setattr(lead, field, value)
            lead.save()
        else:
            lead = DoubleTickLead.objects.create(conversation=conversation, **defaults)
            conversation.current_lead = lead

        DoubleTickMessage.objects.filter(conversation=conversation, lead__isnull=True).update(lead=lead)

        if has_area:
            conversation.status = DoubleTickConversation.Status.QUALIFIED
            conversation.pending_reason = ""
            conversation.requires_manual_attention = False
        elif conversation.raw_area:
            conversation.status = DoubleTickConversation.Status.AREA_UNMATCHED
            conversation.pending_reason = DoubleTickConversation.PendingReason.UNMATCHED_LOCATION
            conversation.requires_manual_attention = True
        else:
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = (
                DoubleTickConversation.PendingReason.GREETING_ONLY
                if latest_customer and PendingConversationService.is_greeting_only(latest_customer.text)
                else DoubleTickConversation.PendingReason.MISSING_LOCATION
            )
            conversation.requires_manual_attention = True
        conversation.save(update_fields=["current_lead", "status", "pending_reason", "requires_manual_attention", "updated_at"])
        _activity(
            conversation=conversation,
            lead=lead,
            user=user,
            action=DoubleTickActivity.Action.LEAD_QUALIFIED,
            new_status=lead.status,
        )
        if has_area and distribute:
            LeadDistributionService.distribute(lead, user=user)
        return lead

    @staticmethod
    @transaction.atomic
    def qualify_conversation(conversation, user=None, distribute=True):
        if not conversation.area_confirmed or not conversation.matched_area_id:
            raise ValidationError("Conversation cannot be qualified until a CRM area is confirmed.")
        return LeadQualificationService.ensure_conversation_lead(conversation, user=user, distribute=distribute)


class LeadDistributionService:
    """Make a qualified area lead visible to mapped branches/managers/devices."""

    @staticmethod
    def _get_or_create_visibility(**kwargs):
        existing = DoubleTickLeadVisibility.objects.filter(**kwargs).first()
        if existing:
            return existing, False
        try:
            with transaction.atomic():
                return DoubleTickLeadVisibility.objects.create(**kwargs), True
        except IntegrityError:
            return DoubleTickLeadVisibility.objects.filter(**kwargs).first(), False

    @staticmethod
    def _active_mappings_for_area(lead_area):
        return list(DoubleTickLeadAreaBranch.objects.select_related("branch").filter(
            lead_area=lead_area,
            lead_area__is_active=True,
            lead_area__is_deleted=False,
            is_active=True,
            receives_leads=True,
            branch__is_active=True,
            branch__is_deleted=False,
        ).order_by("priority", "branch__spa_name"))

    @staticmethod
    def _ensure_fallback_mappings(lead):
        if not getattr(settings, "DOUBLETICK_AUTO_MAP_BRANCH_FROM_LOCATION", True):
            return []
        branch_candidates = AreaMatchingService.find_branch_candidates(
            lead.raw_area or lead.area or (lead.matched_area.name if lead.matched_area else ""),
            lead.raw_city or lead.city or (lead.matched_area.city if lead.matched_area else ""),
        )
        created_mappings = []
        for branch in branch_candidates:
            mapping, created = DoubleTickLeadAreaBranch.objects.get_or_create(
                lead_area=lead.matched_area,
                branch=branch,
                defaults={
                    "is_active": True,
                    "receives_leads": True,
                    "notes": "Auto-created during DoubleTick distribution from branch city/area/spa metadata.",
                },
            )
            if created:
                created_mappings.append(mapping)
        return created_mappings

    @staticmethod
    @transaction.atomic
    def distribute(lead, user=None):
        lead = DoubleTickLead.objects.select_for_update(of=("self",)).select_related("matched_area", "conversation").get(pk=lead.pk)
        if not lead.matched_area_id:
            lead.status = DoubleTickLead.Status.UNASSIGNED
            lead.save(update_fields=["status", "updated_at"])
            _activity(lead=lead, action=DoubleTickActivity.Action.MANUAL_ATTENTION_REQUIRED, note="Lead has no matched area.")
            DoubleTickDistributionAudit.objects.create(
                lead=lead,
                conversation=lead.conversation,
                status=DoubleTickDistributionAudit.Status.SUCCESS,
                failure_reason="Lead has no matched area; kept in manual queue.",
            )
            return lead

        mappings = LeadDistributionService._active_mappings_for_area(lead.matched_area)
        auto_created_mappings = []
        if not mappings:
            auto_created_mappings = LeadDistributionService._ensure_fallback_mappings(lead)
            mappings = LeadDistributionService._active_mappings_for_area(lead.matched_area)
        if not mappings:
            lead.status = DoubleTickLead.Status.FAILED
            lead.save(update_fields=["status", "updated_at"])
            _activity(
                lead=lead,
                action=DoubleTickActivity.Action.PROCESSING_FAILED,
                note="No active branch mapping found.",
                metadata={
                    "raw_city": lead.raw_city or lead.city,
                    "raw_area": lead.raw_area or lead.area,
                    "matched_area": str(lead.matched_area_id),
                },
            )
            DoubleTickDistributionAudit.objects.create(
                lead=lead,
                conversation=lead.conversation,
                matched_area=lead.matched_area,
                status=DoubleTickDistributionAudit.Status.FAILED,
                failure_reason="No active branch mapping found.",
                metadata={
                    "raw_city": lead.raw_city or lead.city,
                    "raw_area": lead.raw_area or lead.area,
                    "matched_area": str(lead.matched_area_id),
                },
            )
            return lead

        mode = lead.matched_area.distribution_mode or DoubleTickLeadArea.DistributionMode.BROADCAST_CLAIM
        if mode == DoubleTickLeadArea.DistributionMode.MANUAL:
            lead.status = DoubleTickLead.Status.UNASSIGNED
            lead.distributed_at = timezone.now()
            lead.save(update_fields=["status", "distributed_at", "updated_at"])
            DoubleTickDistributionAudit.objects.create(
                lead=lead,
                conversation=lead.conversation,
                matched_area=lead.matched_area,
                status=DoubleTickDistributionAudit.Status.SUCCESS,
                mapped_branch_count=len(mappings),
                failure_reason="Manual distribution mode; lead kept in admin/manager queue.",
            )
            _activity(conversation=lead.conversation, lead=lead, user=user, action=DoubleTickActivity.Action.LEAD_DISTRIBUTED, metadata={"mode": mode})
            return lead

        if mode == DoubleTickLeadArea.DistributionMode.ROUND_ROBIN:
            last_audit = DoubleTickDistributionAudit.objects.filter(
                matched_area=lead.matched_area,
                metadata__round_robin_branch_id__isnull=False,
            ).order_by("-created_at").first()
            last_branch_id = (last_audit.metadata or {}).get("round_robin_branch_id") if last_audit else None
            start_index = 0
            if last_branch_id:
                for index, mapping in enumerate(mappings):
                    if str(mapping.branch_id) == str(last_branch_id):
                        start_index = (index + 1) % len(mappings)
                        break
            mappings = [mappings[start_index]]

        User = get_user_model()
        notified_count = 0
        notification_failure_count = 0
        created_visibility_count = 0
        visibility_count = 0
        branch_ids = []
        for mapping in mappings:
            branch = mapping.branch
            branch_ids.append(str(branch.id))
            _, created = LeadDistributionService._get_or_create_visibility(lead=lead, branch=branch)
            created_visibility_count += 1 if created else 0
            visibility_count += 1
            managers = User.objects.filter(role="spa_manager", branch=branch, is_active=True)
            devices = Device.objects.filter(branch=branch, is_active=True, is_blocked=False, is_registered=True)
            for manager in managers:
                visibility, created = LeadDistributionService._get_or_create_visibility(lead=lead, branch=branch, user=manager)
                created_visibility_count += 1 if created else 0
                visibility_count += 1
                ok, error = (True, "") if visibility.notification_sent else send_lead_notification(lead, manager)
                visibility.notification_sent = ok
                visibility.notification_error = error
                visibility.notified_at = visibility.notified_at or timezone.now()
                visibility.save(update_fields=["notification_sent", "notification_error", "notified_at", "updated_at"])
                notified_count += 1 if ok else 0
                notification_failure_count += 0 if ok else 1
                _activity(
                    conversation=lead.conversation,
                    lead=lead,
                    user=manager,
                    branch=branch,
                    action=DoubleTickActivity.Action.NOTIFICATION_SENT if ok else DoubleTickActivity.Action.PROCESSING_FAILED,
                    note=error,
                )
            for device in devices:
                visibility, created = LeadDistributionService._get_or_create_visibility(lead=lead, branch=branch, device=device)
                created_visibility_count += 1 if created else 0
                visibility_count += 1
                ok, error = (True, "") if visibility.notification_sent else send_lead_notification(lead, device)
                visibility.notification_sent = ok
                visibility.notification_error = error
                visibility.notified_at = visibility.notified_at or timezone.now()
                visibility.save(update_fields=["notification_sent", "notification_error", "notified_at", "updated_at"])
                notified_count += 1 if ok else 0
                notification_failure_count += 0 if ok else 1
                _activity(
                    conversation=lead.conversation,
                    lead=lead,
                    device=device,
                    branch=branch,
                    action=DoubleTickActivity.Action.NOTIFICATION_SENT if ok else DoubleTickActivity.Action.PROCESSING_FAILED,
                    note=error,
                )

        lead.status = DoubleTickLead.Status.AVAILABLE
        lead.distributed_at = timezone.now()
        lead.save(update_fields=["status", "distributed_at", "updated_at"])
        if lead.conversation_id:
            lead.conversation.status = DoubleTickConversation.Status.DISTRIBUTED
            lead.conversation.save(update_fields=["status", "updated_at"])
        _activity(
            conversation=lead.conversation,
            lead=lead,
            user=user,
            action=DoubleTickActivity.Action.LEAD_DISTRIBUTED,
            metadata={
                "mapped_branch_count": len(mappings),
                "visibility_count": visibility_count,
                "created_visibility_count": created_visibility_count,
                "notified_count": notified_count,
                "notification_failure_count": notification_failure_count,
                "auto_created_mapping_count": len(auto_created_mappings),
            },
        )
        DoubleTickDistributionAudit.objects.create(
            lead=lead,
            conversation=lead.conversation,
            matched_area=lead.matched_area,
            status=DoubleTickDistributionAudit.Status.PARTIAL if notification_failure_count else DoubleTickDistributionAudit.Status.SUCCESS,
            mapped_branch_count=len(mappings),
            visibility_count=visibility_count,
            notification_success_count=notified_count,
            notification_failure_count=notification_failure_count,
            metadata={
                "branch_ids": branch_ids,
                "mode": mode,
                "round_robin_branch_id": branch_ids[0] if mode == DoubleTickLeadArea.DistributionMode.ROUND_ROBIN and branch_ids else "",
                "auto_created_mapping_ids": [str(mapping.id) for mapping in auto_created_mappings],
                "raw_city": lead.raw_city or lead.city,
                "raw_area": lead.raw_area or lead.area,
            },
        )
        return lead


class LeadClaimService:
    """Concurrency-safe claim/release/contact operations."""

    CONTACT_ACTION_TRANSITIONS = {
        "open": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
        },
        "start_contact": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
        },
        "contacted": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "no_answer": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "customer_busy": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "follow_up": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "booked": {
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "not_interested": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "lost": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
        },
        "close": {
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
            DoubleTickLead.Status.BOOKED,
            DoubleTickLead.Status.NOT_INTERESTED,
            DoubleTickLead.Status.LOST,
        },
    }

    @staticmethod
    def _ensure_visible_to_user(lead, user):
        if getattr(user, "role", None) in ["super_admin", "admin"]:
            if lead.current_branch_id:
                return lead.current_branch
            visibility = DoubleTickLeadVisibility.objects.filter(lead=lead, is_visible=True).select_related("branch").first()
            if visibility:
                return visibility.branch
            raise PermissionDenied("Lead is not visible to any branch.")
        if getattr(user, "role", None) == "spa_manager" and user.branch_id:
            if DoubleTickLeadVisibility.objects.filter(lead=lead, branch=user.branch, is_visible=True).exists():
                return user.branch
        if getattr(user, "role", None) == "area_manager":
            branch_ids = user.area_branches.values_list("id", flat=True)
            visibility = DoubleTickLeadVisibility.objects.filter(lead=lead, branch_id__in=branch_ids, is_visible=True).first()
            if visibility:
                return visibility.branch
        raise PermissionDenied("You are not allowed to claim this lead.")

    @staticmethod
    @transaction.atomic
    def claim(lead_id, user, device=None):
        if not getattr(user, "role", None):
            raise PermissionDenied("A CRM user is required to claim a DoubleTick lead.")
        lead = DoubleTickLead.objects.select_for_update().get(pk=lead_id)
        if lead.status not in [DoubleTickLead.Status.AVAILABLE, DoubleTickLead.Status.RELEASED]:
            raise Conflict("Lead is not available for claim.")
        if DoubleTickLeadAssignment.objects.select_for_update().filter(lead=lead, is_active=True).exists():
            raise Conflict("Lead is already claimed.")

        branch = LeadClaimService._ensure_visible_to_user(lead, user)
        attempt_number = (DoubleTickLeadAssignment.objects.filter(lead=lead).aggregate(max_attempt=Max("attempt_number"))["max_attempt"] or 0) + 1
        assignment = DoubleTickLeadAssignment.objects.create(
            lead=lead,
            attempt_number=attempt_number,
            branch=branch,
            assigned_user=user,
            assigned_device=device,
            status=DoubleTickLeadAssignment.Status.CLAIMED,
            is_active=True,
            claimed_at=timezone.now(),
        )
        lead.status = DoubleTickLead.Status.CLAIMED
        lead.current_branch = branch
        lead.current_user = user
        lead.current_device = device
        lead.active_assignment = assignment
        lead.claimed_at = assignment.claimed_at
        lead.assigned_branch = branch
        lead.assigned_user = user
        lead.assigned_device = device
        lead.assigned_at = assignment.claimed_at
        lead.save()
        _activity(lead=lead, assignment=assignment, user=user, device=device, branch=branch, action=DoubleTickActivity.Action.CLAIMED, new_status=lead.status)
        return assignment

    @staticmethod
    def _active_assignment_for_user(lead, user):
        assignment = DoubleTickLeadAssignment.objects.filter(lead=lead, is_active=True).first()
        if not assignment:
            raise Conflict("Lead is not currently claimed.")
        if getattr(user, "role", None) in ["super_admin", "admin"]:
            return assignment
        if assignment.assigned_user_id != user.id:
            raise PermissionDenied("Only the active manager can perform this action.")
        return assignment

    @staticmethod
    @transaction.atomic
    def update_contact_status(lead_id, user, action, note="", device=None):
        lead = DoubleTickLead.objects.select_for_update().get(pk=lead_id)
        assignment = LeadClaimService._active_assignment_for_user(lead, user)
        now = timezone.now()
        if action not in LeadClaimService.CONTACT_ACTION_TRANSITIONS:
            raise ValidationError("Unsupported lead action.")
        if lead.status not in LeadClaimService.CONTACT_ACTION_TRANSITIONS[action]:
            raise Conflict(f"Action '{action}' is not allowed while lead status is '{lead.status}'.")
        if action == "open":
            lead.status = DoubleTickLead.Status.OPENED
            lead.opened_at = lead.opened_at or now
            assignment.status = DoubleTickLeadAssignment.Status.OPENED
            assignment.opened_at = assignment.opened_at or now
            activity = DoubleTickActivity.Action.VIEWED
        elif action == "start_contact":
            lead.status = DoubleTickLead.Status.CONTACTING
            assignment.status = DoubleTickLeadAssignment.Status.CONTACT_STARTED
            assignment.contact_started_at = assignment.contact_started_at or now
            activity = DoubleTickActivity.Action.CONTACT_STARTED
        elif action in ["contacted", "no_answer", "customer_busy"]:
            lead.status = DoubleTickLead.Status.CONTACTED if action == "contacted" else DoubleTickLead.Status.FOLLOW_UP
            lead.contacted_at = now if action == "contacted" else lead.contacted_at
            assignment.status = DoubleTickLeadAssignment.Status.CONTACTED if action == "contacted" else DoubleTickLeadAssignment.Status.FOLLOW_UP
            assignment.contact_completed_at = now if action == "contacted" else assignment.contact_completed_at
            assignment.outcome = action
            activity = DoubleTickActivity.Action.STATUS_UPDATED
        elif action == "follow_up":
            lead.status = DoubleTickLead.Status.FOLLOW_UP
            lead.follow_up_at = now
            assignment.status = DoubleTickLeadAssignment.Status.FOLLOW_UP
            assignment.follow_up_at = now
            activity = DoubleTickActivity.Action.FOLLOW_UP_ADDED
        elif action == "booked":
            lead.status = DoubleTickLead.Status.BOOKED
            lead.booked_at = now
            assignment.status = DoubleTickLeadAssignment.Status.BOOKED
            assignment.outcome = action
            activity = DoubleTickActivity.Action.BOOKED
        elif action in ["not_interested", "lost", "close"]:
            lead.status = DoubleTickLead.Status.NOT_INTERESTED if action == "not_interested" else DoubleTickLead.Status.LOST if action == "lost" else DoubleTickLead.Status.CLOSED
            lead.closed_at = now if action == "close" else lead.closed_at
            assignment.status = DoubleTickLeadAssignment.Status.LOST if action != "close" else DoubleTickLeadAssignment.Status.CLOSED
            assignment.outcome = action
            activity = DoubleTickActivity.Action.LOST if action != "close" else DoubleTickActivity.Action.CLOSED
        assignment.remarks = note or assignment.remarks
        assignment.save()
        lead.save()
        _activity(lead=lead, assignment=assignment, user=user, device=device, branch=assignment.branch, action=activity, new_status=lead.status, note=note)
        return lead

    @staticmethod
    @transaction.atomic
    def release(lead_id, user, reason="", device=None):
        lead = DoubleTickLead.objects.select_for_update().get(pk=lead_id)
        assignment = LeadClaimService._active_assignment_for_user(lead, user)
        now = timezone.now()
        assignment.is_active = False
        assignment.status = DoubleTickLeadAssignment.Status.RELEASED
        assignment.released_at = now
        assignment.release_reason = reason
        assignment.save()
        lead.status = DoubleTickLead.Status.AVAILABLE
        lead.current_branch = None
        lead.current_user = None
        lead.current_device = None
        lead.active_assignment = None
        lead.save()
        _activity(lead=lead, assignment=assignment, user=user, device=device, branch=assignment.branch, action=DoubleTickActivity.Action.RELEASED, new_status=lead.status, note=reason)
        return lead


class DoubleTickChatService:
    """Local-first chat history and optional provider sync."""

    @staticmethod
    def get_chat(conversation):
        return conversation.messages.select_related("sent_by", "customer").order_by("message_timestamp", "received_at", "sent_at", "created_at")

    @staticmethod
    def sync_chat(conversation):
        """
        Placeholder for on-demand provider sync.

        Local webhook history remains available even if the external API is not
        configured. A real DoubleTick history endpoint can be connected here
        without changing the conversation API.
        """
        if not getattr(settings, "DOUBLETICK_API_KEY", ""):
            return {"status": "synced", "created_messages": 0, "updated_messages": 0, "warning": "DoubleTick API key not configured."}
        return {"status": "synced", "created_messages": 0, "updated_messages": 0}


class DoubleTickReplyService:
    """Manual CRM replies through DoubleTick."""

    @staticmethod
    def _send_text(conversation, text):
        api_key = getattr(settings, "DOUBLETICK_API_KEY", "")
        base_url = getattr(settings, "DOUBLETICK_BASE_URL", "https://public.doubletick.io").rstrip("/")
        if not api_key:
            raise ValidationError("DoubleTick API key is not configured. Send an approved template or configure DOUBLETICK_API_KEY.")

        endpoint = getattr(settings, "DOUBLETICK_SEND_TEXT_ENDPOINT", "/whatsapp/message/text")
        url = endpoint if str(endpoint).startswith(("http://", "https://")) else f"{base_url}/{str(endpoint).lstrip('/')}"
        recipient = _digits_only(conversation.customer.normalized_phone or conversation.customer.phone_number)
        waba_number = _digits_only(
            getattr(settings, "DOUBLETICK_SEND_FROM_WABA_NUMBER", "")
            or (conversation.channel.waba_number if conversation.channel else "")
        )
        if not recipient:
            raise ValidationError("Customer WhatsApp number is missing, so DoubleTick request location cannot be sent.")
        payload = {
            "to": recipient,
            "message": text,
            "messageType": "TEXT",
        }
        if waba_number:
            payload["wabaNumber"] = waba_number

        auth_header = getattr(settings, "DOUBLETICK_AUTH_HEADER", "Authorization") or "Authorization"
        auth_scheme = getattr(settings, "DOUBLETICK_AUTH_SCHEME", "Bearer")
        auth_value = api_key if not auth_scheme else f"{auth_scheme} {api_key}"

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", auth_header: auth_value},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")
                return {"status_code": response.status, "body": body}
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")[:500]
            except Exception:
                body = ""
            details = f"DoubleTick rejected the send request with HTTP {exc.code}."
            if exc.code == 403:
                details += " Check API key permissions, WABA number, endpoint, and whether the message must be sent as an approved template."
            if body:
                details += f" Provider response: {body}"
            raise ValidationError(details) from exc
        except urllib.error.URLError as exc:
            raise ValidationError(f"DoubleTick send failed: {exc.reason}") from exc

    @staticmethod
    def reply(conversation, user, text, message_type="text"):
        if not getattr(user, "is_authenticated", False):
            raise PermissionDenied("A CRM user is required to reply to DoubleTick conversations.")
        now = timezone.now()
        message = DoubleTickMessage.objects.create(
            conversation=conversation,
            customer=conversation.customer,
            direction=DoubleTickMessage.Direction.OUTBOUND,
            origin=DoubleTickMessage.Origin.AGENT,
            message_type=message_type,
            text=text,
            status=DoubleTickMessage.Status.QUEUED,
            sent_by=user,
            sender_display_name=getattr(user, "full_name", "") or "Associate",
            customer_number=conversation.customer.phone_number,
            waba_number=conversation.channel.waba_number if conversation.channel else "",
            message_timestamp=now,
            sent_at=now,
            raw_payload={},
        )
        try:
            response = DoubleTickReplyService._send_text(conversation, text)
            message.status = DoubleTickMessage.Status.SENT
            message.raw_payload = response
            response_body = response.get("body", "")
            if response_body:
                try:
                    parsed_body = json.loads(response_body)
                    provider_id = first_value(parsed_body, ["messageId", "id", "data.messageId", "message.id"])
                    if provider_id:
                        message.message_id = str(provider_id)
                        message.dt_message_id = message.dt_message_id or str(provider_id)
                except ValueError:
                    pass
        except Exception as exc:
            message.status = DoubleTickMessage.Status.FAILED
            message.failed_at = timezone.now()
            message.failure_reason = str(exc)
            message.save()
            _activity(conversation=conversation, action=DoubleTickActivity.Action.PROCESSING_FAILED, user=user, note=str(exc), metadata={"message_id": str(message.id)})
            raise
        message.save()
        conversation.team_last_replied_at = now
        conversation.last_agent_message_at = now
        conversation.last_message_at = now
        conversation.status = DoubleTickConversation.Status.AWAITING_CUSTOMER
        conversation.save(update_fields=["team_last_replied_at", "last_agent_message_at", "last_message_at", "status", "updated_at"])
        _activity(conversation=conversation, action=DoubleTickActivity.Action.MANUAL_REPLY_SENT, user=user, metadata={"message_id": str(message.id)})
        return message

    @staticmethod
    def request_location(conversation, user):
        message = getattr(settings, "DOUBLETICK_LOCATION_REQUEST_MESSAGE", LOCATION_REQUEST_MESSAGE)
        reply = DoubleTickReplyService.reply(conversation, user, message)
        conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
        conversation.status = DoubleTickConversation.Status.AWAITING_CUSTOMER
        conversation.save(update_fields=["pending_reason", "status", "updated_at"])
        _activity(conversation=conversation, action=DoubleTickActivity.Action.LOCATION_REQUESTED, user=user)
        return reply


def find_channel_from_payload(payload):
    waba_number = first_value(payload, [
        "waba_number",
        "wabaNumber",
        "channel.waba_number",
        "data.wabaNumber",
        "data.channel.waba_number",
        "to",
        "from",
    ])
    channel = _channel_from_waba_number(waba_number)
    if channel:
        return channel
    active_channels = list(DoubleTickChannel.objects.filter(is_active=True)[:2])
    return active_channels[0] if len(active_channels) == 1 else None


@transaction.atomic
def create_or_update_lead_from_webhook(payload):
    """
    Process DoubleTick webhooks idempotently.

    Inbound messages update conversations and may qualify/distribute leads only
    after area confirmation. Status-only webhooks update messages and never
    create leads.
    """
    event_type = get_event_type(payload)
    event_id = get_event_id(payload)
    event_class = DoubleTickWebhookClassifier.classify(payload)

    webhook_log = None
    if event_id:
        webhook_log = DoubleTickWebhookLog.objects.filter(doubletick_event_id=event_id).select_for_update().first()
        if webhook_log and webhook_log.processed:
            webhook_log.error_message = "duplicate_event_skipped"
            return webhook_log.lead, webhook_log

    if not webhook_log:
        webhook_log = DoubleTickWebhookLog.objects.create(
            event_type=event_type,
            doubletick_event_id=event_id,
            payload=payload,
        )

    _activity(action=DoubleTickActivity.Action.WEBHOOK_RECEIVED, metadata={"event_type": event_type, "event_class": event_class})

    try:
        if event_class in ["message_status_update", "outgoing_api_message", "outgoing_agent_message"]:
            message = DoubleTickConversationService.update_outbound_status(payload)
            webhook_log.message = message
            if message:
                webhook_log.conversation = message.conversation
                webhook_log.lead = message.lead
            webhook_log.processed = True
            webhook_log.save(update_fields=["conversation", "lead", "message", "processed", "updated_at"])
            return None, webhook_log

        inbound_classes = ["incoming_customer_message", "interactive_reply", "template_reply", "flow_response", "customer_custom_field_updated"]
        if event_class not in inbound_classes:
            webhook_log.processed = True
            webhook_log.save(update_fields=["processed", "updated_at"])
            return None, webhook_log

        conversation, message, created_message = DoubleTickConversationService.upsert_inbound_message(payload)
        webhook_log.conversation = conversation
        webhook_log.message = message
        if not conversation.channel_id:
            webhook_log.error_message = "channel_not_found"
            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PROCESSING_FAILED,
                note="DoubleTick channel not found for webhook payload.",
                metadata={
                    "reason": "channel_not_found",
                    "waba_candidates": [
                        normalize_waba_number(first_value(payload, [path]))
                        for path in [
                            "wabaNumber",
                            "waba_number",
                            "channel.waba_number",
                            "data.wabaNumber",
                            "data.channel.waba_number",
                            "to",
                            "from",
                        ]
                        if first_value(payload, [path])
                    ],
                },
            )

        if not created_message:
            if conversation.current_lead_id and message.lead_id != conversation.current_lead_id:
                message.lead = conversation.current_lead
                message.save(update_fields=["lead", "updated_at"])
            webhook_log.processed = True
            webhook_log.save(update_fields=["conversation", "message", "error_message", "processed", "updated_at"])
            return conversation.current_lead, webhook_log

        parsed_payload = parse_doubletick_payload(payload)
        inbound_text = conversation.raw_area or parsed_payload.get("area") or message.text
        match_result = CRMLocationMatchEngine.classify_message(
            inbound_text,
            raw_city=conversation.raw_city or parsed_payload.get("city", ""),
            channel=conversation.channel,
        )
        if parsed_payload.get("service_name") and match_result.get("classification") in ["unknown", "greeting"]:
            match_result.update(
                classification="service_action",
                confidence=0.9,
                reason="payload_service",
                raw_service=parsed_payload["service_name"],
                should_request_location=not bool(conversation.raw_area),
            )
        AreaMatchingService.apply_match_result(conversation, match_result)
        lead = LeadQualificationService.ensure_conversation_lead(
            conversation,
            matched_area=conversation.matched_area,
            distribute=bool(conversation.area_confirmed and conversation.matched_area_id),
        )
        if match_result.get("classification") in ["branch"] and match_result.get("current_branch"):
            lead.current_branch = match_result["current_branch"]
            lead.assigned_branch = match_result["current_branch"]
            lead.save(update_fields=["current_branch", "assigned_branch", "updated_at"])
        AutoLocationRequestService.request_if_needed(conversation, match_result)

        webhook_log.lead = lead
        if lead and message.lead_id != lead.id:
            message.lead = lead
            message.save(update_fields=["lead", "updated_at"])

        # Simple duplicate detection: if a previous lead with the same
        # normalized phone exists, mark this new lead as a duplicate and
        # point `duplicate_of` to the earlier lead. This is intentionally
        # conservative and non-blocking; failures here should not break
        # webhook processing.
        try:
            if lead and lead.normalized_phone:
                existing_lead = DoubleTickLead.objects.filter(normalized_phone=lead.normalized_phone).exclude(id=lead.id).order_by("created_at").first()
                if existing_lead:
                    lead.is_duplicate = True
                    lead.duplicate_of = existing_lead
                    lead.save(update_fields=["is_duplicate", "duplicate_of", "updated_at"])
        except Exception:
            pass

        if getattr(settings, "DOUBLETICK_AUTO_REPLY_ENABLED", False):
            try:
                from apps.bots.services import BotEngine

                BotEngine.handle_incoming_message(conversation, lead, message)
            except Exception as bot_exc:
                _activity(
                    conversation=conversation,
                    lead=lead,
                    action=DoubleTickActivity.Action.PROCESSING_FAILED,
                    note=f"Bot processing failed: {bot_exc}",
                )

        webhook_log.processed = True
        webhook_log.save(update_fields=["conversation", "message", "lead", "error_message", "processed", "updated_at"])
        return lead, webhook_log
    except Exception as exc:
        webhook_log.error_message = str(exc)
        webhook_log.save(update_fields=["error_message", "updated_at"])
        _activity(action=DoubleTickActivity.Action.PROCESSING_FAILED, note=str(exc), metadata={"webhook_log": str(webhook_log.id)})
        raise

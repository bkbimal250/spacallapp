import re

from rest_framework import serializers

from apps.callrouting.models import (
    RoutingAttempt,
    RoutingCandidate,
    RoutingEvent,
    RoutingRequest,
    RoutingRule,
    RoutingWhatsAppMessage,
)


def mask_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) >= 10:
        return f"XXXXX{digits[-5:]}"
    if len(digits) >= 4:
        return f"XXXX{digits[-4:]}"
    return ""


class BranchSnapshotSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    spa_name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    area = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)


class RoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRule
        fields = [
            "id",
            "name",
            "description",
            "routing_type",
            "enabled",
            "start_time",
            "end_time",
            "max_recommendations",
            "cooldown_minutes",
            "whatsapp_enabled",
            "dry_run",
            "priority",
            "template_name",
            "template_language",
            "template_version",
            "active_from",
            "active_until",
            "created_at",
            "updated_at",
        ]


class RoutingCandidateSerializer(serializers.ModelSerializer):
    branch = BranchSnapshotSerializer(read_only=True)

    class Meta:
        model = RoutingCandidate
        fields = [
            "id",
            "branch",
            "rank",
            "relevance_score",
            "is_open",
            "is_eligible",
            "is_selected",
            "rejection_reason",
            "metadata",
            "evaluated_at",
        ]


class RoutingAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingAttempt
        fields = [
            "id",
            "attempt_number",
            "status",
            "started_at",
            "completed_at",
            "error_code",
            "error_message",
            "metadata",
        ]


class RoutingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingEvent
        fields = ["id", "event_type", "message", "metadata", "created_at"]


class RoutingWhatsAppMessageSerializer(serializers.ModelSerializer):
    recipient_phone_masked = serializers.SerializerMethodField()

    class Meta:
        model = RoutingWhatsAppMessage
        fields = [
            "id",
            "recipient_phone_masked",
            "template_name",
            "template_language",
            "template_payload",
            "provider_message_id",
            "status",
            "queued_at",
            "sent_at",
            "delivered_at",
            "read_at",
            "failed_at",
            "failure_reason",
            "provider_payload",
            "created_at",
            "updated_at",
        ]

    def get_recipient_phone_masked(self, obj):
        return mask_phone(obj.recipient_phone)


class RoutingRequestListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    phone_masked = serializers.SerializerMethodField()
    original_spa = serializers.CharField(source="source_branch.spa_name", read_only=True)
    location = serializers.SerializerMethodField()
    routing_rule_name = serializers.CharField(source="routing_rule.name", read_only=True)
    selected_spas = serializers.SerializerMethodField()
    whatsapp_status = serializers.SerializerMethodField()

    class Meta:
        model = RoutingRequest
        fields = [
            "id",
            "call_log_id",
            "lead_id",
            "created_at",
            "call_time",
            "completed_at",
            "customer_name",
            "phone_masked",
            "original_spa",
            "location",
            "source_branch_open",
            "routing_rule_name",
            "routing_type",
            "status",
            "rejection_reason",
            "selected_spas",
            "whatsapp_status",
        ]

    def get_customer_name(self, obj):
        return getattr(obj.contact, "name", "") or "Unknown"

    def get_phone_masked(self, obj):
        raw_phone = obj.normalized_phone or getattr(obj.call_log, "phone_number", "")
        return mask_phone(raw_phone)

    def get_location(self, obj):
        branch = obj.source_branch
        if not branch:
            return ""
        return ", ".join(part for part in [branch.area, branch.city] if part)

    def get_selected_spas(self, obj):
        candidates = getattr(obj, "prefetched_candidates", None) or obj.candidates.all()
        return [
            {
                "id": str(candidate.branch_id),
                "name": candidate.branch.spa_name,
                "rank": candidate.rank,
            }
            for candidate in candidates
            if candidate.is_selected and candidate.branch_id
        ]

    def get_whatsapp_status(self, obj):
        messages = getattr(obj, "prefetched_whatsapp_messages", None) or obj.whatsapp_messages.all()
        first = messages[0] if messages else None
        return first.status if first else ""


class RoutingRequestDetailSerializer(RoutingRequestListSerializer):
    source_branch = BranchSnapshotSerializer(read_only=True)
    routing_rule = RoutingRuleSerializer(read_only=True)
    candidates = RoutingCandidateSerializer(many=True, read_only=True)
    attempts = RoutingAttemptSerializer(many=True, read_only=True)
    events = RoutingEventSerializer(many=True, read_only=True)
    whatsapp_messages = RoutingWhatsAppMessageSerializer(many=True, read_only=True)
    call_log = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()

    class Meta(RoutingRequestListSerializer.Meta):
        fields = RoutingRequestListSerializer.Meta.fields + [
            "normalized_phone",
            "source_open_checked_at",
            "metadata",
            "source_branch",
            "routing_rule",
            "call_log",
            "contact",
            "lead",
            "candidates",
            "attempts",
            "events",
            "whatsapp_messages",
        ]

    def get_call_log(self, obj):
        call_log = obj.call_log
        return {
            "id": str(call_log.id),
            "phone_masked": mask_phone(call_log.phone_number),
            "call_type": call_log.call_type,
            "duration": call_log.duration,
            "sim_slot": call_log.sim_slot,
            "call_time": call_log.call_time,
            "device_id": str(call_log.device_id) if call_log.device_id else "",
            "device_uid": getattr(call_log.device, "device_id", ""),
            "phone_name": getattr(call_log.device, "phone_name", ""),
        }

    def get_contact(self, obj):
        if not obj.contact_id:
            return None
        return {
            "id": str(obj.contact_id),
            "name": obj.contact.name,
            "phone_masked": mask_phone(obj.contact.phone_number),
            "email": obj.contact.email,
            "city": obj.contact.city,
        }

    def get_lead(self, obj):
        if not obj.lead_id:
            return None
        return {
            "id": str(obj.lead_id),
            "status": obj.lead.status,
            "remarks": obj.lead.remarks,
            "booking_date": obj.lead.booking_date,
        }

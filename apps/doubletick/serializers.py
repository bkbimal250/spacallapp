import re

from rest_framework import serializers

from .models import (
    DoubleTickActivity,
    DoubleTickAreaAlias,
    DoubleTickChannel,
    DoubleTickConversation,
    DoubleTickCustomer,
    DoubleTickDistributionAudit,
    DoubleTickLead,
    DoubleTickLeadActivity,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadAssignment,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
    DoubleTickWebhookLog,
)


def normalize_area_value(value):
    return re.sub(r"\s+", " ", (value or "").strip().lower())


class DoubleTickChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleTickChannel
        fields = "__all__"


class DoubleTickCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleTickCustomer
        fields = "__all__"


class DoubleTickLeadAreaSerializer(serializers.ModelSerializer):
    alias_count = serializers.IntegerField(read_only=True)
    branch_mapping_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DoubleTickLeadArea
        fields = "__all__"
        read_only_fields = ["normalized_name"]

    def create(self, validated_data):
        validated_data["normalized_name"] = normalize_area_value(validated_data.get("name"))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "name" in validated_data:
            validated_data["normalized_name"] = normalize_area_value(validated_data.get("name"))
        return super().update(instance, validated_data)


class DoubleTickAreaAliasSerializer(serializers.ModelSerializer):
    lead_area_name = serializers.CharField(source="lead_area.name", read_only=True)
    channel_name = serializers.CharField(source="channel.name", read_only=True)

    class Meta:
        model = DoubleTickAreaAlias
        fields = "__all__"
        read_only_fields = ["normalized_alias"]

    def create(self, validated_data):
        validated_data["normalized_alias"] = normalize_area_value(validated_data.get("alias"))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "alias" in validated_data:
            validated_data["normalized_alias"] = normalize_area_value(validated_data.get("alias"))
        return super().update(instance, validated_data)


class DoubleTickLeadAreaBranchSerializer(serializers.ModelSerializer):
    lead_area_name = serializers.CharField(source="lead_area.name", read_only=True)
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    branch_area = serializers.CharField(source="branch.area", read_only=True)
    branch_city = serializers.CharField(source="branch.city", read_only=True)
    branch_state = serializers.CharField(source="branch.state", read_only=True)

    class Meta:
        model = DoubleTickLeadAreaBranch
        fields = "__all__"

    def validate(self, attrs):
        lead_area = attrs.get("lead_area") or getattr(self.instance, "lead_area", None)
        branch = attrs.get("branch") or getattr(self.instance, "branch", None)
        if lead_area:
            if getattr(lead_area, "is_deleted", False):
                raise serializers.ValidationError({"lead_area": "Deleted lead areas cannot receive mappings."})
            if not lead_area.is_active:
                raise serializers.ValidationError({"lead_area": "Inactive lead areas cannot receive mappings."})
        if branch:
            if getattr(branch, "is_deleted", False):
                raise serializers.ValidationError({"branch": "Deleted branches cannot receive DoubleTick leads."})
            if not branch.is_active:
                raise serializers.ValidationError({"branch": "Inactive branches cannot receive DoubleTick leads."})
        if lead_area and branch:
            duplicate = DoubleTickLeadAreaBranch.objects.filter(lead_area=lead_area, branch=branch)
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError({"branch": "This branch is already mapped to the selected lead area."})
        return attrs


class DoubleTickMessageSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.full_name", read_only=True)
    sender = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    status_timestamps = serializers.SerializerMethodField()

    class Meta:
        model = DoubleTickMessage
        fields = "__all__"

    def get_sender(self, obj):
        if obj.origin == DoubleTickMessage.Origin.CUSTOMER:
            customer = obj.customer
            name = ""
            if customer:
                name = customer.customer_name or customer.whatsapp_name or customer.phone_number
            return {"name": name or obj.customer_number or "Customer", "type": "customer"}
        if obj.sender_display_name:
            name = obj.sender_display_name
        elif obj.sent_by:
            name = obj.sent_by.full_name
        elif obj.origin == DoubleTickMessage.Origin.BOT:
            name = "Bot"
        elif obj.origin == DoubleTickMessage.Origin.API:
            name = "API"
        elif obj.origin == DoubleTickMessage.Origin.AGENT:
            name = "Associate"
        else:
            name = "System"
        return {"name": name, "type": obj.origin or obj.direction}

    def get_timestamp(self, obj):
        value = obj.message_timestamp or obj.received_at or obj.sent_at or obj.created_at
        return value.isoformat() if value else None

    def get_status_timestamps(self, obj):
        return {
            "sent_at": obj.sent_at.isoformat() if obj.sent_at else None,
            "delivered_at": obj.delivered_at.isoformat() if obj.delivered_at else None,
            "read_at": obj.read_at.isoformat() if obj.read_at else None,
            "failed_at": obj.failed_at.isoformat() if obj.failed_at else None,
        }


class DoubleTickActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)

    class Meta:
        model = DoubleTickActivity
        fields = "__all__"


class DoubleTickConversationListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.customer_name", read_only=True)
    phone_number = serializers.CharField(source="customer.phone_number", read_only=True)
    normalized_phone = serializers.CharField(source="customer.normalized_phone", read_only=True)
    matched_area_name = serializers.CharField(source="matched_area.name", read_only=True)
    channel_waba_number = serializers.CharField(source="channel.waba_number", read_only=True)
    latest_customer_message = serializers.SerializerMethodField()
    suggested_match = serializers.SerializerMethodField()
    match_confidence = serializers.SerializerMethodField()
    match_reason = serializers.SerializerMethodField()

    class Meta:
        model = DoubleTickConversation
        fields = [
            "id",
            "customer",
            "customer_name",
            "phone_number",
            "normalized_phone",
            "channel",
            "channel_waba_number",
            "status",
            "pending_reason",
            "priority",
            "raw_city",
            "raw_area",
            "raw_service",
            "matched_area",
            "matched_area_name",
            "latest_customer_message",
            "suggested_match",
            "match_confidence",
            "match_reason",
            "last_message_at",
            "last_customer_message_at",
            "unread_count",
            "requires_manual_attention",
            "bot_completed",
            "area_confirmed",
            "assigned_support_user",
            "current_lead",
            "created_at",
        ]

    def _location_metadata(self, obj):
        payload = obj.raw_payload if isinstance(obj.raw_payload, dict) else {}
        return payload.get("location_match", {}) or {}

    def get_latest_customer_message(self, obj):
        messages = [
            message for message in obj.messages.all()
            if message.direction == DoubleTickMessage.Direction.INBOUND
        ]
        if not messages:
            return ""
        message = max(
            messages,
            key=lambda item: item.message_timestamp or item.received_at or item.created_at,
        )
        return message.text

    def get_suggested_match(self, obj):
        payload = obj.raw_payload if isinstance(obj.raw_payload, dict) else {}
        return payload.get("suggested_match")

    def get_match_confidence(self, obj):
        return self._location_metadata(obj).get("confidence", 0.0)

    def get_match_reason(self, obj):
        return self._location_metadata(obj).get("reason", "")


class DoubleTickConversationDetailSerializer(DoubleTickConversationListSerializer):
    customer_detail = DoubleTickCustomerSerializer(source="customer", read_only=True)
    recent_messages = serializers.SerializerMethodField()

    class Meta(DoubleTickConversationListSerializer.Meta):
        fields = DoubleTickConversationListSerializer.Meta.fields + [
            "customer_detail",
            "raw_payload",
            "recent_messages",
            "first_message_at",
            "last_agent_message_at",
            "customer_last_replied_at",
            "team_last_replied_at",
        ]

    def get_recent_messages(self, obj):
        messages = obj.messages.order_by("-received_at", "-sent_at", "-created_at")[:10]
        return DoubleTickMessageSerializer(reversed(list(messages)), many=True).data


class DoubleTickLeadListSerializer(serializers.ModelSerializer):
    matched_area_name = serializers.CharField(source="matched_area.name", read_only=True)
    location_status = serializers.SerializerMethodField()
    raw_group = serializers.SerializerMethodField()
    raw_branch = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    spa_name = serializers.SerializerMethodField()
    current_branch_name = serializers.CharField(source="current_branch.spa_name", read_only=True)
    current_user_name = serializers.CharField(source="current_user.full_name", read_only=True)
    current_device_name = serializers.CharField(source="current_device.phone_name", read_only=True)
    assigned_branch_name = serializers.CharField(source="assigned_branch.spa_name", read_only=True)
    assigned_user_name = serializers.CharField(source="assigned_user.full_name", read_only=True)
    assigned_device_name = serializers.CharField(source="assigned_device.phone_name", read_only=True)
    unread_count = serializers.IntegerField(source="conversation.unread_count", read_only=True)
    last_message_at = serializers.DateTimeField(source="conversation.last_message_at", read_only=True)
    can_claim = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()
    can_update_status = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    match_method = serializers.SerializerMethodField()
    match_confidence = serializers.SerializerMethodField()
    match_reason = serializers.SerializerMethodField()
    suggested_match = serializers.SerializerMethodField()
    pending_reason = serializers.CharField(source="conversation.pending_reason", read_only=True)
    android_visibility_count = serializers.SerializerMethodField()
    android_device_count = serializers.SerializerMethodField()
    android_user_count = serializers.SerializerMethodField()
    sent_to_android = serializers.SerializerMethodField()

    class Meta:
        model = DoubleTickLead
        fields = [
            "id",
            "conversation",
            "customer",
            "customer_name",
            "whatsapp_name",
            "phone_number",
            "normalized_phone",
            "initial_message",
            "latest_customer_message",
            "message",
            "raw_city",
            "raw_group",
            "raw_area",
            "raw_branch",
            "raw_service",
            "city",
            "city_name",
            "area",
            "service_name",
            "matched_area",
            "matched_area_name",
            "location_status",
            "group_name",
            "branch_name",
            "spa_name",
            "status",
            "current_branch",
            "current_branch_name",
            "current_user",
            "current_user_name",
            "current_device_name",
            "assigned_branch",
            "assigned_branch_name",
            "assigned_user",
            "assigned_user_name",
            "assigned_device",
            "assigned_device_name",
            "distributed_at",
            "claimed_at",
            "last_message_at",
            "unread_count",
            "can_claim",
            "can_reply",
            "can_update_status",
            "classification",
            "match_method",
            "match_confidence",
            "match_reason",
            "suggested_match",
            "pending_reason",
            "android_visibility_count",
            "android_device_count",
            "android_user_count",
            "sent_to_android",
            "is_duplicate",
            "created_at",
        ]

    def _match_meta(self, obj):
        return (obj.raw_payload or {}).get("location_match", {}) if isinstance(obj.raw_payload, dict) else {}

    def _conversation_payload(self, obj):
        conversation = getattr(obj, "conversation", None)
        return conversation.raw_payload if conversation and isinstance(conversation.raw_payload, dict) else {}

    def _visibility_rows(self, obj):
        return [item for item in obj.visibilities.all() if item.is_visible]

    def get_location_status(self, obj):
        if obj.matched_area_id:
            return "matched"
        if obj.status == DoubleTickLead.Status.UNASSIGNED:
            return "pending"
        return "unknown"

    def get_raw_group(self, obj):
        return self._match_meta(obj).get("raw_group") or ""

    def get_raw_branch(self, obj):
        return self._match_meta(obj).get("raw_branch") or ""

    def get_city_name(self, obj):
        return obj.city or obj.raw_city or (obj.matched_area.city if obj.matched_area else "")

    def get_group_name(self, obj):
        return self.get_raw_group(obj)

    def get_branch_name(self, obj):
        branch = obj.current_branch or obj.assigned_branch
        return branch.spa_name if branch else ""

    def get_spa_name(self, obj):
        return self.get_branch_name(obj)

    def get_classification(self, obj):
        return self._match_meta(obj).get("classification") or self._conversation_payload(obj).get("location_match", {}).get("classification") or "unknown"

    def get_match_method(self, obj):
        return self._match_meta(obj).get("method") or self._conversation_payload(obj).get("location_match", {}).get("method") or "none"

    def get_match_confidence(self, obj):
        value = self._match_meta(obj).get("confidence")
        if value is None:
            value = self._conversation_payload(obj).get("location_match", {}).get("confidence", 0)
        return value or 0

    def get_match_reason(self, obj):
        return self._match_meta(obj).get("reason") or self._conversation_payload(obj).get("location_match", {}).get("reason") or ""

    def get_suggested_match(self, obj):
        return self._conversation_payload(obj).get("suggested_match")

    def get_android_visibility_count(self, obj):
        return len(self._visibility_rows(obj))

    def get_android_device_count(self, obj):
        return sum(1 for item in self._visibility_rows(obj) if item.device_id)

    def get_android_user_count(self, obj):
        return sum(1 for item in self._visibility_rows(obj) if item.user_id)

    def get_sent_to_android(self, obj):
        return any(item.device_id for item in self._visibility_rows(obj))

    def get_can_claim(self, obj):
        return obj.status in [DoubleTickLead.Status.AVAILABLE, DoubleTickLead.Status.RELEASED]

    def get_can_reply(self, obj):
        return bool(obj.conversation_id)

    def get_can_update_status(self, obj):
        return obj.status in [
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
            DoubleTickLead.Status.BOOKED,
            DoubleTickLead.Status.NOT_INTERESTED,
            DoubleTickLead.Status.LOST,
        ]


class DoubleTickMobileMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = DoubleTickMessage
        fields = ["id", "direction", "text", "status", "sender_name", "timestamp"]

    def get_sender_name(self, obj):
        return obj.sender_display_name or getattr(obj.sent_by, "full_name", None) or (
            "Customer" if obj.direction == DoubleTickMessage.Direction.INBOUND else "Team"
        )

    def get_timestamp(self, obj):
        return obj.message_timestamp or obj.received_at or obj.sent_at or obj.created_at


class DoubleTickMobileLeadSerializer(serializers.ModelSerializer):
    lead_id = serializers.UUIDField(source="id", read_only=True)
    phone = serializers.CharField(source="phone_number", read_only=True)
    location_status = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    area_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    spa_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    device_name = serializers.SerializerMethodField()
    is_unclaimed = serializers.SerializerMethodField()
    android_visibility_status = serializers.SerializerMethodField()
    can_claim = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()
    can_update_status = serializers.SerializerMethodField()
    last_message_at = serializers.DateTimeField(source="conversation.last_message_at", read_only=True)
    unread_count = serializers.IntegerField(source="conversation.unread_count", read_only=True)

    class Meta:
        model = DoubleTickLead
        fields = [
            "lead_id",
            "customer_name",
            "phone",
            "latest_customer_message",
            "status",
            "location_status",
            "city_name",
            "group_name",
            "area_name",
            "branch_name",
            "spa_name",
            "owner_name",
            "device_name",
            "is_unclaimed",
            "android_visibility_status",
            "can_claim",
            "can_reply",
            "can_update_status",
            "created_at",
            "last_message_at",
            "unread_count",
        ]

    def _location_area(self, obj):
        return getattr(obj.matched_area, "location_area", None) if obj.matched_area else None

    def _visible_rows(self, obj):
        return [row for row in getattr(obj, "mobile_visibilities", []) if row.is_visible]

    def _display_branch(self, obj):
        branch = obj.current_branch or obj.assigned_branch
        if branch:
            return branch

        device = self.context.get("mobile_device")
        rows = self._visible_rows(obj)
        if device:
            for row in rows:
                if row.device_id == device.id or row.branch_id == device.branch_id:
                    return row.branch
        return rows[0].branch if rows else None

    def get_location_status(self, obj):
        if obj.matched_area_id and self._location_area(obj):
            return "matched"
        if obj.matched_area_id:
            return "legacy_matched"
        return "pending"

    def get_city_name(self, obj):
        location_area = self._location_area(obj)
        return (
            getattr(getattr(location_area, "city", None), "name", None)
            or obj.city
            or obj.raw_city
            or getattr(obj.matched_area, "city", None)
            or "-"
        )

    def get_group_name(self, obj):
        location_area = self._location_area(obj)
        mappings = getattr(location_area, "mobile_group_mappings", []) if location_area else []
        if mappings:
            return mappings[0].group.name
        metadata = (obj.raw_payload or {}).get("location_match", {}) if isinstance(obj.raw_payload, dict) else {}
        return metadata.get("raw_group") or "-"

    def get_area_name(self, obj):
        location_area = self._location_area(obj)
        return getattr(location_area, "name", None) or getattr(obj.matched_area, "name", None) or obj.area or obj.raw_area or "-"

    def get_branch_name(self, obj):
        branch = self._display_branch(obj)
        return getattr(branch, "spa_name", None) or "-"

    def get_spa_name(self, obj):
        return self.get_branch_name(obj)

    def get_owner_name(self, obj):
        owner = obj.current_user or obj.assigned_user
        return getattr(owner, "full_name", None) or "Unclaimed"

    def get_device_name(self, obj):
        device = obj.current_device or obj.assigned_device
        return getattr(device, "phone_name", None) or "-"

    def get_is_unclaimed(self, obj):
        return not bool(obj.current_user_id or obj.current_device_id or obj.active_assignment_id)

    def get_android_visibility_status(self, obj):
        device = self.context.get("mobile_device")
        if device and obj.current_device_id == device.id:
            return "owned"
        user = self.context.get("request_user")
        if user and getattr(user, "is_authenticated", False) and obj.current_user_id == getattr(user, "id", None):
            return "owned"
        return "visible" if self._visible_rows(obj) else "not_visible"

    def get_can_claim(self, obj):
        return self.get_is_unclaimed(obj) and obj.status in [
            DoubleTickLead.Status.AVAILABLE,
            DoubleTickLead.Status.RELEASED,
        ]

    def get_can_reply(self, obj):
        return bool(obj.conversation_id)

    def get_can_update_status(self, obj):
        return not self.get_is_unclaimed(obj) and obj.status in [
            DoubleTickLead.Status.CLAIMED,
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTING,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
            DoubleTickLead.Status.BOOKED,
            DoubleTickLead.Status.NOT_INTERESTED,
            DoubleTickLead.Status.LOST,
        ]


class DoubleTickMobileLeadDetailSerializer(DoubleTickMobileLeadSerializer):
    messages = DoubleTickMobileMessageSerializer(many=True, read_only=True)

    class Meta(DoubleTickMobileLeadSerializer.Meta):
        fields = DoubleTickMobileLeadSerializer.Meta.fields + ["messages"]


class DoubleTickLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleTickLead
        fields = "__all__"
        read_only_fields = [
            "normalized_phone",
            "raw_payload",
            "distributed_at",
            "claimed_at",
            "assigned_at",
            "opened_at",
            "contacted_at",
            "follow_up_at",
            "booked_at",
            "is_duplicate",
            "duplicate_of",
        ]


class DoubleTickLeadDetailSerializer(DoubleTickLeadListSerializer):
    visibilities = serializers.SerializerMethodField()
    active_assignment_detail = serializers.SerializerMethodField()
    customer_detail = DoubleTickCustomerSerializer(source="customer", read_only=True)
    chat_timeline = serializers.SerializerMethodField()
    latest_distribution_audit = serializers.SerializerMethodField()

    class Meta(DoubleTickLeadListSerializer.Meta):
        fields = DoubleTickLeadListSerializer.Meta.fields + [
            "customer_detail",
            "raw_payload",
            "lost_reason",
            "closed_reason",
            "remarks",
            "visibilities",
            "active_assignment",
            "active_assignment_detail",
            "chat_timeline",
            "latest_distribution_audit",
        ]

    def get_visibilities(self, obj):
        return DoubleTickLeadVisibilitySerializer(obj.visibilities.select_related("branch", "user", "device"), many=True).data

    def get_active_assignment_detail(self, obj):
        if not obj.active_assignment_id:
            return None
        return DoubleTickLeadAssignmentSerializer(obj.active_assignment).data

    def get_chat_timeline(self, obj):
        queryset = obj.messages.select_related("sent_by", "customer").order_by("message_timestamp", "received_at", "sent_at", "created_at")
        return DoubleTickMessageSerializer(queryset, many=True).data

    def get_latest_distribution_audit(self, obj):
        audit = obj.distribution_audits.order_by("-created_at").first()
        return DoubleTickDistributionAuditSerializer(audit).data if audit else None


class DoubleTickLeadVisibilitySerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    device_name = serializers.CharField(source="device.phone_name", read_only=True)

    class Meta:
        model = DoubleTickLeadVisibility
        fields = "__all__"


class DoubleTickLeadAssignmentSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)
    assigned_user_name = serializers.CharField(source="assigned_user.full_name", read_only=True)

    class Meta:
        model = DoubleTickLeadAssignment
        fields = "__all__"


class DoubleTickDistributionAuditSerializer(serializers.ModelSerializer):
    lead_phone_number = serializers.CharField(source="lead.phone_number", read_only=True)
    matched_area_name = serializers.CharField(source="matched_area.name", read_only=True)

    class Meta:
        model = DoubleTickDistributionAudit
        fields = "__all__"


class DoubleTickLeadActivitySerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(
        choices=DoubleTickLeadActivity.Action.choices,
        required=False,
        default=DoubleTickLeadActivity.Action.NOTE,
    )
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    device_name = serializers.CharField(source="device.phone_name", read_only=True)

    class Meta:
        model = DoubleTickLeadActivity
        fields = [
            "id",
            "lead",
            "user",
            "user_name",
            "device",
            "device_name",
            "action",
            "note",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "lead", "user", "device", "created_at"]


class DoubleTickLeadStatusUpdateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            "contacted",
            "no_answer",
            "customer_busy",
            "follow_up",
            "booked",
            "not_interested",
            "lost",
            "close",
        ],
        required=False,
    )
    status = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    lost_reason = serializers.CharField(required=False, allow_blank=True)


class DoubleTickLeadAssignSerializer(serializers.Serializer):
    assigned_branch = serializers.UUIDField(required=False, allow_null=True)
    assigned_user = serializers.UUIDField(required=False, allow_null=True)
    assigned_device = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)


class DoubleTickConversationReplySerializer(serializers.Serializer):
    message_type = serializers.CharField(default="text")
    text = serializers.CharField()


class DoubleTickConversationMatchAreaSerializer(serializers.Serializer):
    lead_area_id = serializers.UUIDField()
    save_alias = serializers.BooleanField(default=False)
    raw_alias = serializers.CharField(required=False, allow_blank=True)
    qualify_as_lead = serializers.BooleanField(default=True)


class DoubleTickConversationAssignSupportSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False, allow_null=True)


class DoubleTickWebhookSerializer(serializers.Serializer):
    """Accept flexible DoubleTick JSON payloads."""

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Webhook payload must be a JSON object.")
        return data


class DoubleTickWebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleTickWebhookLog
        fields = "__all__"

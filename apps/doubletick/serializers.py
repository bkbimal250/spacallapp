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
    current_branch_name = serializers.CharField(source="current_branch.spa_name", read_only=True)
    current_user_name = serializers.CharField(source="current_user.full_name", read_only=True)
    assigned_branch_name = serializers.CharField(source="assigned_branch.spa_name", read_only=True)
    assigned_user_name = serializers.CharField(source="assigned_user.full_name", read_only=True)
    assigned_device_name = serializers.CharField(source="assigned_device.phone_name", read_only=True)

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
            "raw_area",
            "raw_service",
            "city",
            "area",
            "service_name",
            "matched_area",
            "matched_area_name",
            "status",
            "current_branch",
            "current_branch_name",
            "current_user",
            "current_user_name",
            "assigned_branch",
            "assigned_branch_name",
            "assigned_user",
            "assigned_user_name",
            "assigned_device",
            "assigned_device_name",
            "distributed_at",
            "claimed_at",
            "is_duplicate",
            "created_at",
        ]


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

    class Meta(DoubleTickLeadListSerializer.Meta):
        fields = DoubleTickLeadListSerializer.Meta.fields + [
            "raw_payload",
            "lost_reason",
            "closed_reason",
            "remarks",
            "visibilities",
            "active_assignment",
            "active_assignment_detail",
        ]

    def get_visibilities(self, obj):
        return DoubleTickLeadVisibilitySerializer(obj.visibilities.select_related("branch", "user", "device"), many=True).data

    def get_active_assignment_detail(self, obj):
        if not obj.active_assignment_id:
            return None
        return DoubleTickLeadAssignmentSerializer(obj.active_assignment).data


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

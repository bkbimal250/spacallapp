from rest_framework import serializers

from .models import DoubleTickLead, DoubleTickLeadActivity, DoubleTickWebhookLog


class DoubleTickLeadListSerializer(serializers.ModelSerializer):
    assigned_branch_name = serializers.CharField(source="assigned_branch.spa_name", read_only=True)
    assigned_user_name = serializers.CharField(source="assigned_user.full_name", read_only=True)
    assigned_device_name = serializers.CharField(source="assigned_device.phone_name", read_only=True)

    class Meta:
        model = DoubleTickLead
        fields = [
            "id",
            "customer_name",
            "whatsapp_name",
            "phone_number",
            "normalized_phone",
            "message",
            "city",
            "area",
            "service_name",
            "source_ad",
            "status",
            "assigned_branch",
            "assigned_branch_name",
            "assigned_user",
            "assigned_user_name",
            "assigned_device",
            "assigned_device_name",
            "assigned_at",
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
            "assigned_at",
            "opened_at",
            "contacted_at",
            "follow_up_at",
            "booked_at",
            "is_duplicate",
            "duplicate_of",
        ]


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


class DoubleTickLeadDetailSerializer(DoubleTickLeadSerializer):
    assigned_branch_name = serializers.CharField(source="assigned_branch.spa_name", read_only=True)
    assigned_user_name = serializers.CharField(source="assigned_user.full_name", read_only=True)
    assigned_device_name = serializers.CharField(source="assigned_device.phone_name", read_only=True)
    activities = DoubleTickLeadActivitySerializer(many=True, read_only=True)

    class Meta(DoubleTickLeadSerializer.Meta):
        fields = "__all__"


class DoubleTickLeadStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            DoubleTickLead.Status.OPENED,
            DoubleTickLead.Status.CONTACTED,
            DoubleTickLead.Status.FOLLOW_UP,
            DoubleTickLead.Status.BOOKED,
            DoubleTickLead.Status.LOST,
        ]
    )
    note = serializers.CharField(required=False, allow_blank=True)
    lost_reason = serializers.CharField(required=False, allow_blank=True)


class DoubleTickLeadAssignSerializer(serializers.Serializer):
    assigned_branch = serializers.UUIDField(required=False, allow_null=True)
    assigned_user = serializers.UUIDField(required=False, allow_null=True)
    assigned_device = serializers.UUIDField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)


class DoubleTickWebhookSerializer(serializers.Serializer):
    """
    Flexible webhook serializer.

    DoubleTick payload shapes may differ by event type, so validation only
    requires the incoming request to be a JSON object.
    """

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Webhook payload must be a JSON object.")
        return data


class DoubleTickWebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleTickWebhookLog
        fields = "__all__"

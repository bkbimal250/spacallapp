from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    user_name = serializers.CharField(source="user.full_name", read_only=True, default=None)
    user_phone = serializers.CharField(source="user.phone_number", read_only=True, default=None)
    recipient_name = serializers.SerializerMethodField()
    recipient_type = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'device', 'device_name', 'branch_name',
            'user', 'user_name', 'user_phone', 'recipient_name', 'recipient_type',
            'title', 'body', 'notification_type', 
            'is_sent', 'firebase_message_id', 'error_message', 
            'created_at'
        ]

    @extend_schema_field(serializers.CharField())
    def get_device_name(self, obj):
        return obj.device.device_id if obj.device else "N/A"

    @extend_schema_field(serializers.CharField())
    def get_branch_name(self, obj):
        if obj.device and obj.device.branch:
            return obj.device.branch.spa_name
        if obj.user and obj.user.branch:
            return obj.user.branch.spa_name
        return "System / Global"

    @extend_schema_field(serializers.CharField())
    def get_recipient_name(self, obj):
        if obj.device:
            return obj.device.phone_name or obj.device.device_id
        if obj.user:
            return obj.user.full_name or obj.user.email
        return "Unknown Recipient"

    @extend_schema_field(serializers.CharField())
    def get_recipient_type(self, obj):
        if obj.device_id:
            return "device"
        if obj.user_id:
            return "user"
        return "unknown"

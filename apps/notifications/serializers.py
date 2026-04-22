from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'device', 'device_name', 'branch_name', 
            'title', 'body', 'notification_type', 
            'is_sent', 'firebase_message_id', 'error_message', 
            'created_at'
        ]

    def get_device_name(self, obj):
        return obj.device.device_id if obj.device else "N/A"

    def get_branch_name(self, obj):
        if obj.device and obj.device.branch:
            return obj.device.branch.spa_name
        return "System / Global"

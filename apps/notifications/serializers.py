from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_id', read_only=True)
    branch_name = serializers.CharField(source='device.branch.spa_name', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'device', 'device_name', 'branch_name', 
            'title', 'body', 'notification_type', 
            'is_sent', 'firebase_message_id', 'error_message', 
            'created_at'
        ]

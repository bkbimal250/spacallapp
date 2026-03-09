from rest_framework import serializers
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True)

    class Meta:
        model = Device
        fields = (
            "id", "branch", "branch_name", "device_id", "registration_token", "sim_1_number", "sim_2_number",
            "last_sync", "last_heartbeat", "is_registered", "is_active", "is_blocked",
            "status", "is_online", "created_at"
        )

class ClaimRegistrationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=32, required=True)


from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True, allow_null=True)
    branch_is_active = serializers.BooleanField(source='branch.is_active', read_only=True, default=False)

    @extend_schema_field(serializers.CharField())
    def get_status(self, obj):
        return obj.status

    @extend_schema_field(serializers.BooleanField())
    def get_is_online(self, obj):
        return obj.is_online

    status = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = (
            "id", "branch", "branch_name", "phone_name", "device_id", "registration_token", "sim_1_number", "sim_2_number",
            "last_sync", "last_heartbeat", "is_registered", "is_active", "is_blocked",
            "status", "is_online", "created_at", "branch_is_active"
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure branch_name is never None if we want a default string
        if ret.get('branch_name') is None:
            ret['branch_name'] = "Unassigned"
        return ret

class ClaimRegistrationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=32, required=True)


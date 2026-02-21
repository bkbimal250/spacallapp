from rest_framework import serializers
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True)

    class Meta:
        model = Device
        fields = '__all__'

class ClaimRegistrationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=32, required=True)


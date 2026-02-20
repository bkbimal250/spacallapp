from rest_framework import serializers
from .models import DeviceEvent, DeviceHealth

class DeviceEventSerializer(serializers.ModelSerializer):
    device_uid = serializers.CharField(source='device.device_id', read_only=True)
    branch_name = serializers.CharField(source='device.branch.spa_name', read_only=True)

    class Meta:
        model = DeviceEvent
        fields = '__all__'

class DeviceHealthSerializer(serializers.ModelSerializer):
     class Meta:
        model = DeviceHealth
        fields = '__all__'

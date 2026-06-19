from rest_framework import serializers
from .models import DeviceEvent, DeviceHealth

class DeviceEventSerializer(serializers.ModelSerializer):
    device_uid = serializers.CharField(source='device.device_id', read_only=True)
    device_name = serializers.CharField(source='device.phone_name', read_only=True)
    branch_name = serializers.CharField(source='device.branch.spa_name', read_only=True)
    event_label = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = DeviceEvent
        fields = '__all__'

class DeviceHealthSerializer(serializers.ModelSerializer):
     class Meta:
        model = DeviceHealth
        fields = '__all__'

from rest_framework import serializers
from .models import CallLog

class CallLogSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True)
    device_uid = serializers.CharField(source='device.device_id', read_only=True)

    class Meta:
        model = CallLog
        fields = '__all__'

from rest_framework import serializers
from .models import CallLog

class CallLogSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True)
    branch_code = serializers.CharField(source='branch.code', read_only=True)
    device_uid = serializers.CharField(source='device.device_id', read_only=True)
    phone_name = serializers.CharField(source='device.phone_name', read_only=True)
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    lead_status = serializers.SerializerMethodField()
    lead_id = serializers.SerializerMethodField()
    receiver_number = serializers.SerializerMethodField()

    class Meta:
        model = CallLog
        fields = [
            'id', 'branch', 'branch_name', 'branch_code', 'device', 'device_uid', 
            'phone_name', 'contact', 'contact_name', 'phone_number', 'call_type', 
            'duration', 'sim_slot', 'receiver_number', 'call_time', 
            'call_hash', 'lead_status', 'lead_id', 'created_at'
        ]

    def get_receiver_number(self, obj):
        if not obj.device:
            return None
        # We mapped slots to 1 and 2 in the view
        if obj.sim_slot == 1:
            return obj.device.sim_1_number
        elif obj.sim_slot == 2:
            return obj.device.sim_2_number
        return None

    def get_lead_status(self, obj):
        try:
            return obj.lead.status
        except Exception:
            return None

    def get_lead_id(self, obj):
        try:
            return obj.lead.id
        except Exception:
            return None

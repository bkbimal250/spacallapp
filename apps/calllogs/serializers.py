from drf_spectacular.utils import extend_schema_field
from apps.devices.models import Device
from rest_framework import serializers
from .models import CallLog

class CallLogSerializer(serializers.ModelSerializer):
    """Full detail serializer for CallLog."""
    branch_name = serializers.ReadOnlyField(source='branch.spa_name')
    branch_code = serializers.ReadOnlyField(source='branch.code')
    device_uid = serializers.ReadOnlyField(source='device.device_id')
    phone_name = serializers.ReadOnlyField(source='device.phone_name')
    sim_1_number = serializers.ReadOnlyField(source='device.sim_1_number')
    sim_2_number = serializers.ReadOnlyField(source='device.sim_2_number')
    contact_name = serializers.ReadOnlyField(source='contact.name')
    
    # Optimized relation access (requires select_related('lead'))
    lead_status = serializers.ReadOnlyField(source='lead.status')
    lead_id = serializers.ReadOnlyField(source='lead.id')
    
    receiver_number = serializers.SerializerMethodField()
    call_time_label = serializers.SerializerMethodField()
    call_time_warning = serializers.SerializerMethodField()

    class Meta:
        model = CallLog
        fields = [
            'id', 'branch', 'branch_name', 'branch_code', 'device', 'device_uid', 
            'phone_name', 'sim_1_number', 'sim_2_number', 'contact', 'contact_name', 'phone_number', 'call_type',
            'duration', 'sim_slot', 'receiver_number', 'call_time', 
            'device_reported_call_time', 'is_time_invalid', 'invalid_time_reason',
            'call_time_label', 'call_time_warning',
            'call_hash', 'lead_status', 'lead_id', 'created_at'
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_receiver_number(self, obj):
        if not obj.device:
            return None
        if obj.sim_slot == 1:
            return obj.device.sim_1_number
        elif obj.sim_slot == 2:
            return obj.device.sim_2_number
        return None

    def get_call_time_label(self, obj):
        return "Invalid device time" if obj.is_time_invalid else None

    def get_call_time_warning(self, obj):
        if obj.is_time_invalid:
            return "This phone sent a future call time. Please check phone date/time settings."
        return None


class CallLogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for dashboard list views.
    Reduced field count and optimized relation access to minimize payload.
    """
    branch_name = serializers.ReadOnlyField(source='branch.spa_name')
    contact_name = serializers.ReadOnlyField(source='contact.name')
    lead_status = serializers.ReadOnlyField(source='lead.status')
    lead_id = serializers.ReadOnlyField(source='lead.id')
    device_uid = serializers.ReadOnlyField(source='device.device_id')
    phone_name = serializers.ReadOnlyField(source='device.phone_name')
    sim_1_number = serializers.ReadOnlyField(source='device.sim_1_number')
    sim_2_number = serializers.ReadOnlyField(source='device.sim_2_number')
    followup_status = serializers.ReadOnlyField(source='followup_status.sla_status')
    is_followed_up = serializers.ReadOnlyField(source='followup_status.is_followed_up')
    call_time_label = serializers.SerializerMethodField()
    call_time_warning = serializers.SerializerMethodField()
    

    class Meta:
        model = CallLog
        fields = [
            'id', 'phone_number', 'contact_name', 'call_type', 'duration', 'device_uid', 'phone_name',
            'sim_slot', 'sim_1_number', 'sim_2_number',
            'call_time', 'device_reported_call_time', 'is_time_invalid', 'invalid_time_reason',
            'call_time_label', 'call_time_warning',
            'created_at', 'branch_name', 'lead_status', 'lead_id', 'followup_status', 'is_followed_up'
        ]

    def get_call_time_label(self, obj):
        return "Invalid device time" if obj.is_time_invalid else None

    def get_call_time_warning(self, obj):
        if obj.is_time_invalid:
            return "This phone sent a future call time. Please check phone date/time settings."
        return None


class CallLogSyncItemSerializer(serializers.Serializer):
    """
    Validates the Android sync payload without changing the public endpoint.
    The view still owns branch/device assignment and duplicate handling.
    """
    phone_number = serializers.CharField(max_length=20)
    call_type = serializers.ChoiceField(choices=["incoming", "outgoing", "missed", "rejected"])
    duration = serializers.IntegerField(min_value=0, default=0)
    sim_slot = serializers.IntegerField(required=False, default=1)
    call_time = serializers.DateTimeField(required=False)
    call_time_ms = serializers.IntegerField(required=False, min_value=0)
    call_hash = serializers.CharField(max_length=64)

    def validate(self, attrs):
        if attrs.get("call_time_ms") is None and attrs.get("call_time") is None:
            raise serializers.ValidationError({
                "call_time": "Either call_time or call_time_ms is required."
            })
        return attrs


class MissedCallFollowUpSerializer(serializers.ModelSerializer):
    """Serializer for tracking and reporting missed call follow-ups."""
    phone_number = serializers.ReadOnlyField(source='missed_call.phone_number')
    missed_call_time = serializers.ReadOnlyField(source='missed_call.call_time')
    branch_name = serializers.ReadOnlyField(source='branch.spa_name')
    followup_call_time = serializers.ReadOnlyField(source='followup_call.call_time')

    class Meta:
        from .models import MissedCallFollowUp
        model = MissedCallFollowUp
        fields = [
            'id', 'missed_call', 'phone_number', 'missed_call_time', 'branch', 
            'branch_name', 'followup_call', 'followup_call_time', 'is_followed_up', 
            'first_followup_time', 'followup_attempt_count', 'sla_status', 
            'notification_step', 'created_at'
        ]

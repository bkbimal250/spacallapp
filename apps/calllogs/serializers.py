from rest_framework import serializers
from .models import CallLog

class CallLogSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.spa_name', read_only=True)
    device_uid = serializers.CharField(source='device.device_id', read_only=True)
    receiver_number = serializers.SerializerMethodField()

    class Meta:
        model = CallLog
        fields = '__all__'

    def get_receiver_number(self, obj):
        if not obj.device:
            return None
        # We mapped slots to 1 and 2 in the view
        if obj.sim_slot == 1:
            return obj.device.sim_1_number
        elif obj.sim_slot == 2:
            return obj.device.sim_2_number
        return None

from rest_framework import serializers
from .models import LeadManagement
from apps.calllogs.serializers import CallLogSerializer

class LeadManagementSerializer(serializers.ModelSerializer):
    """Full detail serializer for LeadManagement."""
    branch_name = serializers.ReadOnlyField(source='branch.spa_name')
    contact_name = serializers.ReadOnlyField(source='contact.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    updated_by_name = serializers.ReadOnlyField(source='updated_by.full_name')
    phone_number = serializers.ReadOnlyField(source='calllog.phone_number')
    call_type = serializers.ReadOnlyField(source='calllog.call_type')

    class Meta:
        model = LeadManagement
        fields = '__all__'
        read_only_fields = ('created_by', 'updated_by')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        return super().update(instance, validated_data)


class LeadManagementListSerializer(serializers.ModelSerializer):
    """Minimal serializer for Lead Management dashbaord list."""
    branch_name = serializers.ReadOnlyField(source='branch.spa_name')
    contact_name = serializers.ReadOnlyField(source='contact.name')
    phone_number = serializers.ReadOnlyField(source='calllog.phone_number')
    call_type = serializers.ReadOnlyField(source='calllog.call_type')

    class Meta:
        model = LeadManagement
        fields = [
            'id', 'status', 'booking_date', 'branch_name', 
            'contact_name', 'phone_number', 'call_type', 'created_at'
        ]

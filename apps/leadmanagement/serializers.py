from rest_framework import serializers
from .models import LeadManagement
from apps.calllogs.serializers import CallLogSerializer

class LeadManagementSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='calllog.branch.spa_name', read_only=True)
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    # Extra fields for the app to see the correlated phone number directly
    phone_number = serializers.CharField(source='calllog.phone_number', read_only=True)
    call_type = serializers.CharField(source='calllog.call_type', read_only=True)
    
    # Alternatively you can nest simple calllog data
    # calllog_details = CallLogSerializer(source='calllog', read_only=True)

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

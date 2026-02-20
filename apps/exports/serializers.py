from rest_framework import serializers
from .models import ExportJob # Assuming model

class ExportJobSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ExportJob
        fields = '__all__'

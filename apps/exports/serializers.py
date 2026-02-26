from rest_framework import serializers
from .models import ExportJob # Assuming model

class ExportJobSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    filters = serializers.SerializerMethodField()
    
    class Meta:
        model = ExportJob
        fields = '__all__'

    def get_filters(self, obj):
        if not obj.error_message:
            return None
        try:
            import ast
            return ast.literal_eval(obj.error_message)
        except:
            return None

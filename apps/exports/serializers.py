from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import ExportJob # Assuming model

class ExportJobSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    filters = serializers.SerializerMethodField()
    
    class Meta:
        model = ExportJob
        fields = '__all__'

    @extend_schema_field(serializers.DictField())
    def get_filters(self, obj) -> dict:
        if not obj.error_message:
            return {}
        try:
            import ast
            return ast.literal_eval(obj.error_message)
        except:
            return {}

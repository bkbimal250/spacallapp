from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
import ast
import json
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
            filters = json.loads(obj.error_message)
        except (TypeError, ValueError, json.JSONDecodeError):
            try:
                filters = ast.literal_eval(obj.error_message)
            except (SyntaxError, ValueError):
                return {}

        if not isinstance(filters, dict):
            return {}
        return {key: value for key, value in filters.items() if value not in [None, ""]}

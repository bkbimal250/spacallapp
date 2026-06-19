from rest_framework import serializers
from .models import Branch, BranchGroups
from drf_spectacular.utils import extend_schema_field

class BranchGroupSerializer(serializers.ModelSerializer):
    @extend_schema_field(serializers.IntegerField())
    def get_branch_count(self, obj):
        return getattr(obj, 'branch_count', 0)

    branch_count = serializers.SerializerMethodField()

    class Meta:
        model = BranchGroups
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    branch_group_name = serializers.ReadOnlyField(source='branch_group.name')

    class Meta:
        model = Branch
        fields = '__all__'

class BranchListSerializer(serializers.ModelSerializer):
    """
    Lean serializer for branch list view.
    Includes only essential fields to prevent N+1 queries for excluded fields.
    """
    branch_group_name = serializers.ReadOnlyField(source='branch_group.name')

    class Meta:
        model = Branch
        fields = [
            "id", "spa_name", "code", "city", "area", "state", "postal_code", "address", "phone",
            "is_active", "branch_group", "branch_group_name"
        ]

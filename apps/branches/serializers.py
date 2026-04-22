from rest_framework import serializers
from .models import Branch, BranchGroups

class BranchGroupSerializer(serializers.ModelSerializer):
    branch_count = serializers.ReadOnlyField()

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
            "id", "spa_name", "code", "city", "state", "is_active", "branch_group", "branch_group_name"
        ]

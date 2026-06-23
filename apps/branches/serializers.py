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

    # Normalized location FK read-only details
    location_state_name = serializers.ReadOnlyField(source='location_state.name')
    location_city_name = serializers.ReadOnlyField(source='location_city.name')
    location_group_name = serializers.ReadOnlyField(source='location_group.name')
    location_area_name = serializers.ReadOnlyField(source='location_area.name')

    class Meta:
        model = Branch
        fields = [
            'id', 'spa_name', 'code', 'state', 'city', 'area',
            'postal_code', 'address', 'phone', 'is_active',
            'branch_group', 'branch_group_name',
            # Normalized location FKs
            'location_state', 'location_state_name',
            'location_city', 'location_city_name',
            'location_group', 'location_group_name',
            'location_area', 'location_area_name',
            'created_at', 'updated_at',
        ]


class BranchListSerializer(serializers.ModelSerializer):
    """
    Lean serializer for branch list view.
    Includes only essential fields to prevent N+1 queries for excluded fields.
    """
    branch_group_name = serializers.ReadOnlyField(source='branch_group.name')

    # Normalized location FK read-only details (lightweight for list)
    location_state_name = serializers.ReadOnlyField(source='location_state.name')
    location_city_name = serializers.ReadOnlyField(source='location_city.name')
    location_group_name = serializers.ReadOnlyField(source='location_group.name')
    location_area_name = serializers.ReadOnlyField(source='location_area.name')

    class Meta:
        model = Branch
        fields = [
            "id", "spa_name", "code", "city", "area", "state", "postal_code", "address", "phone",
            "is_active", "branch_group", "branch_group_name",
            # Normalized location FKs
            "location_state", "location_state_name",
            "location_city", "location_city_name",
            "location_group", "location_group_name",
            "location_area", "location_area_name",
        ]

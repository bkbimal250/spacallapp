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
        extra_kwargs = {
            'state': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'area': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        location_state = attrs.get('location_state') or getattr(self.instance, 'location_state', None)
        location_city = attrs.get('location_city') or getattr(self.instance, 'location_city', None)
        location_area = attrs.get('location_area') or getattr(self.instance, 'location_area', None)

        if location_state:
            attrs['state'] = location_state.name
        if location_city:
            attrs['city'] = location_city.name
        if location_area:
            attrs['area'] = location_area.name

        state = attrs.get('state') or getattr(self.instance, 'state', '')
        city = attrs.get('city') or getattr(self.instance, 'city', '')
        if not state:
            raise serializers.ValidationError({'location_state': 'State is required.'})
        if not city:
            raise serializers.ValidationError({'location_city': 'City is required.'})

        return attrs


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

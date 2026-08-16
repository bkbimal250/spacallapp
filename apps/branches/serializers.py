from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from rest_framework import serializers
from .models import Branch, BranchGroups, BranchOperatingHours
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
    operating_hours_configured = serializers.IntegerField(read_only=True, default=0)

    # Normalized location FK read-only details
    location_state_name = serializers.ReadOnlyField(source='location_state.name')
    location_city_name = serializers.ReadOnlyField(source='location_city.name')
    location_group_name = serializers.ReadOnlyField(source='location_group.name')
    location_area_name = serializers.ReadOnlyField(source='location_area.name')

    class Meta:
        model = Branch
        fields = [
            'id', 'spa_name', 'code', 'state', 'city', 'area',
            'postal_code', 'address', 'phone', 'shared_link', 'is_active',
            'operating_hours_configured',
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
    operating_hours_configured = serializers.IntegerField(read_only=True, default=0)

    # Normalized location FK read-only details (lightweight for list)
    location_state_name = serializers.ReadOnlyField(source='location_state.name')
    location_city_name = serializers.ReadOnlyField(source='location_city.name')
    location_group_name = serializers.ReadOnlyField(source='location_group.name')
    location_area_name = serializers.ReadOnlyField(source='location_area.name')

    class Meta:
        model = Branch
        fields = [
            "id", "spa_name", "code", "city", "area", "state", "postal_code", "address", "phone", "shared_link",
            "is_active", "operating_hours_configured", "branch_group", "branch_group_name",
            # Normalized location FKs
            "location_state", "location_state_name",
            "location_city", "location_city_name",
            "location_group", "location_group_name",
            "location_area", "location_area_name",
        ]


class BranchOperatingHoursSerializer(serializers.ModelSerializer):
    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)
    is_overnight = serializers.BooleanField(read_only=True)

    class Meta:
        model = BranchOperatingHours
        fields = [
            "id",
            "weekday",
            "weekday_label",
            "is_closed",
            "is_24_hours",
            "opens_at",
            "closes_at",
            "timezone",
            "is_active",
            "is_overnight",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "weekday_label", "is_overnight", "created_at", "updated_at"]

    def validate_timezone(self, value):
        try:
            ZoneInfo(value or settings.TIME_ZONE)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError("Invalid IANA timezone.") from exc
        return value or settings.TIME_ZONE

    def validate(self, attrs):
        is_closed = attrs.get("is_closed", getattr(self.instance, "is_closed", False))
        is_24_hours = attrs.get("is_24_hours", getattr(self.instance, "is_24_hours", False))
        opens_at = attrs.get("opens_at", getattr(self.instance, "opens_at", None))
        closes_at = attrs.get("closes_at", getattr(self.instance, "closes_at", None))

        if is_closed or is_24_hours:
            attrs["opens_at"] = None
            attrs["closes_at"] = None
            return attrs

        if not opens_at or not closes_at:
            raise serializers.ValidationError("opens_at and closes_at are required when the branch is open.")
        if opens_at == closes_at:
            raise serializers.ValidationError("opens_at and closes_at cannot be the same for normal open hours.")
        return attrs


class BranchWeeklyOperatingHoursSerializer(serializers.Serializer):
    timezone = serializers.CharField(required=False, allow_blank=True)
    operating_hours = BranchOperatingHoursSerializer(many=True)

    def validate_timezone(self, value):
        try:
            ZoneInfo(value or settings.TIME_ZONE)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError("Invalid IANA timezone.") from exc
        return value or settings.TIME_ZONE

    def validate_operating_hours(self, value):
        weekdays = [item["weekday"] for item in value]
        if sorted(weekdays) != list(range(7)):
            raise serializers.ValidationError("A complete Monday to Sunday schedule is required.")
        return value

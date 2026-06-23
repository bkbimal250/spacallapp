# apps/locations/serializers.py

from rest_framework import serializers

from .models import (
    Area,
    AreaAlias,
    BranchCoverageArea,
    City,
    CityAlias,
    LocationGroup,
    LocationGroupArea,
    LocationMatchIgnorePhrase,
    State,
    normalize_location_name,
)


class StateMiniSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="name", read_only=True)
    value = serializers.CharField(source="id", read_only=True)

    class Meta:
        model = State
        fields = ["id", "value", "label", "name", "is_active"]


class CityMiniSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="name", read_only=True)
    value = serializers.CharField(source="id", read_only=True)
    state_name = serializers.CharField(source="state.name", read_only=True)

    class Meta:
        model = City
        fields = [
            "id",
            "value",
            "label",
            "state",
            "state_name",
            "name",
            "is_active",
        ]


class AreaMiniSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="name", read_only=True)
    value = serializers.CharField(source="id", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)

    class Meta:
        model = Area
        fields = [
            "id",
            "value",
            "label",
            "city",
            "city_name",
            "state_name",
            "name",
            "is_active",
        ]


class LocationGroupMiniSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="name", read_only=True)
    value = serializers.CharField(source="id", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)

    class Meta:
        model = LocationGroup
        fields = [
            "id",
            "value",
            "label",
            "city",
            "city_name",
            "state_name",
            "name",
            "is_active",
        ]


class StateSerializer(serializers.ModelSerializer):
    city_count = serializers.SerializerMethodField()
    area_count = serializers.SerializerMethodField()
    group_count = serializers.SerializerMethodField()
    branch_coverage_count = serializers.SerializerMethodField()

    class Meta:
        model = State
        fields = [
            "id",
            "name",
            "normalized_name",
            "slug",
            "code",
            "is_active",
            "priority",
            "city_count",
            "area_count",
            "group_count",
            "branch_coverage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "normalized_name",
            "created_at",
            "updated_at",
        ]

    def get_city_count(self, obj):
        annotated = getattr(obj, "city_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.cities.filter(is_deleted=False).count()

    def get_area_count(self, obj):
        annotated = getattr(obj, "area_count_cached", None)
        if annotated is not None:
            return annotated
        return Area.objects.filter(city__state=obj, is_deleted=False).count()

    def get_group_count(self, obj):
        annotated = getattr(obj, "group_count_cached", None)
        if annotated is not None:
            return annotated
        return LocationGroup.objects.filter(city__state=obj, is_deleted=False).count()

    def get_branch_coverage_count(self, obj):
        annotated = getattr(obj, "branch_coverage_count_cached", None)
        if annotated is not None:
            return annotated
        return BranchCoverageArea.objects.filter(
            area__city__state=obj,
            is_deleted=False,
            is_active=True,
        ).count()

    def validate_name(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("State name cannot be empty.")
        return value


class StateListSerializer(StateSerializer):
    class Meta(StateSerializer.Meta):
        fields = [
            "id",
            "name",
            "code",
            "is_active",
            "priority",
            "city_count",
            "area_count",
            "group_count",
        ]


class CityAliasSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)

    class Meta:
        model = CityAlias
        fields = [
            "id",
            "city",
            "city_name",
            "state_name",
            "alias",
            "normalized_alias",
            "language",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_alias", "created_at", "updated_at"]

    def validate_alias(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("Alias cannot be empty.")
        return value


class CitySerializer(serializers.ModelSerializer):
    state_detail = StateMiniSerializer(source="state", read_only=True)
    aliases = CityAliasSerializer(many=True, read_only=True)
    area_count = serializers.SerializerMethodField()
    group_count = serializers.SerializerMethodField()
    alias_count = serializers.SerializerMethodField()
    branch_coverage_count = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            "id",
            "state",
            "state_detail",
            "name",
            "normalized_name",
            "slug",
            "is_active",
            "priority",
            "area_count",
            "group_count",
            "alias_count",
            "branch_coverage_count",
            "aliases",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_name", "created_at", "updated_at"]

    def get_area_count(self, obj):
        annotated = getattr(obj, "area_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.areas.filter(is_deleted=False).count()

    def get_group_count(self, obj):
        annotated = getattr(obj, "group_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.location_groups.filter(is_deleted=False).count()

    def get_alias_count(self, obj):
        annotated = getattr(obj, "alias_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.aliases.filter(is_deleted=False).count()

    def get_branch_coverage_count(self, obj):
        annotated = getattr(obj, "branch_coverage_count_cached", None)
        if annotated is not None:
            return annotated
        return BranchCoverageArea.objects.filter(
            area__city=obj,
            is_deleted=False,
            is_active=True,
        ).count()

    def validate_name(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("City name cannot be empty.")
        return value


class CityListSerializer(CitySerializer):
    state_name = serializers.CharField(source="state.name", read_only=True)

    class Meta(CitySerializer.Meta):
        fields = [
            "id",
            "state",
            "state_name",
            "name",
            "is_active",
            "priority",
            "area_count",
            "group_count",
        ]


class AreaAliasSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source="area.name", read_only=True)
    city_name = serializers.CharField(source="area.city.name", read_only=True)
    state_name = serializers.CharField(source="area.city.state.name", read_only=True)

    class Meta:
        model = AreaAlias
        fields = [
            "id",
            "area",
            "area_name",
            "city_name",
            "state_name",
            "alias",
            "normalized_alias",
            "language",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_alias", "created_at", "updated_at"]

    def validate_alias(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("Alias cannot be empty.")
        return value


class AreaSerializer(serializers.ModelSerializer):
    city_detail = CityMiniSerializer(source="city", read_only=True)
    aliases = AreaAliasSerializer(many=True, read_only=True)
    alias_count = serializers.SerializerMethodField()
    group_count = serializers.SerializerMethodField()
    branch_coverage_count = serializers.SerializerMethodField()

    class Meta:
        model = Area
        fields = [
            "id",
            "city",
            "city_detail",
            "name",
            "normalized_name",
            "slug",
            "is_active",
            "priority",
            "alias_count",
            "group_count",
            "branch_coverage_count",
            "aliases",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_name", "created_at", "updated_at"]

    def get_alias_count(self, obj):
        annotated = getattr(obj, "alias_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.aliases.filter(is_deleted=False).count()

    def get_group_count(self, obj):
        annotated = getattr(obj, "group_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.area_groups.filter(is_deleted=False).count()

    def get_branch_coverage_count(self, obj):
        annotated = getattr(obj, "branch_coverage_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.branch_coverages.filter(is_deleted=False, is_active=True).count()

    def validate_name(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("Area name cannot be empty.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        city = attrs.get("city") or getattr(self.instance, "city", None)
        name = attrs.get("name") or getattr(self.instance, "name", "")
        normalized_name = normalize_location_name(name)

        if city and normalized_name:
            existing = Area.objects.filter(
                city=city,
                normalized_name=normalized_name,
                is_deleted=False,
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            existing_area = existing.first()
            if existing_area:
                raise serializers.ValidationError(
                    {
                        "name": [
                            f'Area "{existing_area.name}" already exists in {city.name}.'
                        ],
                        "existing": {
                            "id": str(existing_area.id),
                            "name": existing_area.name,
                            "city": str(city.id),
                            "city_name": city.name,
                        },
                    }
                )

        return attrs


class AreaListSerializer(AreaSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)

    class Meta(AreaSerializer.Meta):
        fields = [
            "id",
            "city",
            "city_name",
            "state_name",
            "name",
            "normalized_name",
            "is_active",
            "priority",
            "group_count",
        ]


class CityAliasListSerializer(CityAliasSerializer):
    class Meta(CityAliasSerializer.Meta):
        fields = [
            "id",
            "city",
            "city_name",
            "state_name",
            "alias",
            "is_active",
        ]


class AreaAliasListSerializer(AreaAliasSerializer):
    class Meta(AreaAliasSerializer.Meta):
        fields = [
            "id",
            "area",
            "area_name",
            "city_name",
            "state_name",
            "alias",
            "is_active",
        ]


class LocationGroupAreaSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    area_name = serializers.CharField(source="area.name", read_only=True)
    city_name = serializers.CharField(source="area.city.name", read_only=True)

    class Meta:
        model = LocationGroupArea
        fields = [
            "id",
            "group",
            "group_name",
            "area",
            "area_name",
            "city_name",
            "is_primary",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        group = attrs.get("group") or getattr(self.instance, "group", None)
        area = attrs.get("area") or getattr(self.instance, "area", None)

        if group and area and group.city_id != area.city_id:
            raise serializers.ValidationError(
                {"area": "Area must belong to the same city as the selected group."}
            )

        return attrs


class LocationGroupAreaListSerializer(LocationGroupAreaSerializer):
    class Meta(LocationGroupAreaSerializer.Meta):
        fields = [
            "id",
            "group",
            "group_name",
            "area",
            "area_name",
            "city_name",
            "is_primary",
            "priority",
        ]


class LocationGroupSerializer(serializers.ModelSerializer):
    city_detail = CityMiniSerializer(source="city", read_only=True)
    group_areas = LocationGroupAreaSerializer(many=True, read_only=True)
    area_count = serializers.SerializerMethodField()
    branch_coverage_count = serializers.SerializerMethodField()

    class Meta:
        model = LocationGroup
        fields = [
            "id",
            "city",
            "city_detail",
            "name",
            "normalized_name",
            "slug",
            "description",
            "is_active",
            "priority",
            "area_count",
            "branch_coverage_count",
            "group_areas",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_name", "created_at", "updated_at"]

    def get_area_count(self, obj):
        annotated = getattr(obj, "area_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.group_areas.filter(is_deleted=False).count()

    def get_branch_coverage_count(self, obj):
        annotated = getattr(obj, "branch_coverage_count_cached", None)
        if annotated is not None:
            return annotated
        return obj.branch_coverages.filter(is_deleted=False, is_active=True).count()

    def validate_name(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("Location group name cannot be empty.")
        return value


class LocationGroupListSerializer(LocationGroupSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    state_name = serializers.CharField(source="city.state.name", read_only=True)

    class Meta(LocationGroupSerializer.Meta):
        fields = [
            "id",
            "city",
            "city_name",
            "state_name",
            "name",
            "description",
            "is_active",
            "priority",
            "area_count",
            "branch_coverage_count",
        ]


class BranchCoverageAreaSerializer(serializers.ModelSerializer):
    branch_label = serializers.SerializerMethodField()
    area_detail = AreaMiniSerializer(source="area", read_only=True)
    location_group_detail = LocationGroupMiniSerializer(
        source="location_group",
        read_only=True,
    )

    area_name = serializers.CharField(source="area.name", read_only=True)
    city_name = serializers.CharField(source="area.city.name", read_only=True)
    state_name = serializers.CharField(source="area.city.state.name", read_only=True)
    location_group_name = serializers.CharField(
        source="location_group.name",
        read_only=True,
    )

    class Meta:
        model = BranchCoverageArea
        fields = [
            "id",
            "content_type",
            "object_id",
            "branch_label",
            "area",
            "area_detail",
            "area_name",
            "city_name",
            "state_name",
            "location_group",
            "location_group_detail",
            "location_group_name",
            "is_primary",
            "is_active",
            "priority",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "branch_label",
            "area_detail",
            "location_group_detail",
            "area_name",
            "city_name",
            "state_name",
            "location_group_name",
            "created_at",
            "updated_at",
        ]

    def get_branch_label(self, obj):
        try:
            return str(obj.branch) if obj.branch else None
        except Exception:
            return None

    def validate(self, attrs):
        area = attrs.get("area") or getattr(self.instance, "area", None)
        group = attrs.get("location_group") or getattr(self.instance, "location_group", None)

        if area and group and area.city_id != group.city_id:
            raise serializers.ValidationError(
                {"location_group": "Location group must belong to the same city as area."}
            )

        return attrs


class LocationMatchIgnorePhraseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationMatchIgnorePhrase
        fields = [
            "id",
            "phrase",
            "normalized_phrase",
            "phrase_type",
            "language",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_phrase", "created_at", "updated_at"]

    def validate_phrase(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("Phrase cannot be empty.")
        return value


class LocationMatchRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    state_id = serializers.UUIDField(required=False, allow_null=True)
    city_id = serializers.UUIDField(required=False, allow_null=True)
    group_id = serializers.UUIDField(required=False, allow_null=True)
    area_id = serializers.UUIDField(required=False, allow_null=True)
    current_node_type = serializers.CharField(required=False, allow_blank=True)

    def validate_text(self, value):
        if not normalize_location_name(value):
            raise serializers.ValidationError("Text cannot be empty.")
        return value


class LocationAnalyticsSerializer(serializers.Serializer):
    states = serializers.DictField()
    cities = serializers.DictField()
    areas = serializers.DictField()
    groups = serializers.DictField()
    city_aliases = serializers.DictField()
    area_aliases = serializers.DictField()
    branch_coverages = serializers.DictField()
    ignore_phrases = serializers.DictField()
    top_states = serializers.ListField()
    top_cities = serializers.ListField()
    top_areas = serializers.ListField()
    suspicious = serializers.DictField()

# apps/locations/filters.py

import django_filters
from django.db.models import Q

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


class StateFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    active = django_filters.BooleanFilter(field_name="is_active")
    code = django_filters.CharFilter(field_name="code", lookup_expr="iexact")

    class Meta:
        model = State
        fields = ["q", "active", "code"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_name__icontains=value)
            | Q(name__icontains=value)
            | Q(code__icontains=value)
        )


class CityFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    state_id = django_filters.UUIDFilter(field_name="state_id")
    state = django_filters.UUIDFilter(field_name="state_id")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = City
        fields = ["q", "state_id", "state", "active"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_name__icontains=value)
            | Q(name__icontains=value)
            | Q(aliases__normalized_alias__icontains=value)
            | Q(aliases__alias__icontains=value)
        ).distinct()


class CityAliasFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    city_id = django_filters.UUIDFilter(field_name="city_id")
    state_id = django_filters.UUIDFilter(field_name="city__state_id")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = CityAlias
        fields = ["q", "city_id", "state_id", "active"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_alias__icontains=value)
            | Q(alias__icontains=value)
            | Q(city__name__icontains=value)
        )


class AreaFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    city_id = django_filters.UUIDFilter(field_name="city_id")
    city = django_filters.UUIDFilter(field_name="city_id")
    state_id = django_filters.UUIDFilter(field_name="city__state_id")
    group_id = django_filters.UUIDFilter(method="filter_group")
    group = django_filters.UUIDFilter(field_name="group_id", method="filter_group")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Area
        fields = ["q", "city_id", "city", "state_id", "group_id", "group", "active"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_name__icontains=value)
            | Q(name__icontains=value)
            | Q(aliases__normalized_alias__icontains=value)
            | Q(aliases__alias__icontains=value)
        ).distinct()

    def filter_group(self, queryset, name, value):
        return queryset.filter(area_groups__group_id=value, area_groups__is_deleted=False)


class AreaAliasFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    area_id = django_filters.UUIDFilter(field_name="area_id")
    city_id = django_filters.UUIDFilter(field_name="area__city_id")
    state_id = django_filters.UUIDFilter(field_name="area__city__state_id")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = AreaAlias
        fields = ["q", "area_id", "city_id", "state_id", "active"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_alias__icontains=value)
            | Q(alias__icontains=value)
            | Q(area__name__icontains=value)
        )


class LocationGroupFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    city_id = django_filters.UUIDFilter(field_name="city_id")
    city = django_filters.UUIDFilter(field_name="city_id")
    state_id = django_filters.UUIDFilter(field_name="city__state_id")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = LocationGroup
        fields = ["q", "city_id", "city", "state_id", "active"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_name__icontains=value)
            | Q(name__icontains=value)
            | Q(description__icontains=value)
        )


class LocationGroupAreaFilter(django_filters.FilterSet):
    group_id = django_filters.UUIDFilter(field_name="group_id")
    area_id = django_filters.UUIDFilter(field_name="area_id")
    city_id = django_filters.UUIDFilter(field_name="area__city_id")
    state_id = django_filters.UUIDFilter(field_name="area__city__state_id")
    primary = django_filters.BooleanFilter(field_name="is_primary")

    class Meta:
        model = LocationGroupArea
        fields = ["group_id", "area_id", "city_id", "state_id", "primary"]


class BranchCoverageAreaFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    content_type = django_filters.NumberFilter(field_name="content_type_id")
    object_id = django_filters.CharFilter(field_name="object_id")
    area_id = django_filters.UUIDFilter(field_name="area_id")
    city_id = django_filters.UUIDFilter(field_name="area__city_id")
    state_id = django_filters.UUIDFilter(field_name="area__city__state_id")
    group_id = django_filters.UUIDFilter(field_name="location_group_id")
    primary = django_filters.BooleanFilter(field_name="is_primary")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = BranchCoverageArea
        fields = [
            "q",
            "content_type",
            "object_id",
            "area_id",
            "city_id",
            "state_id",
            "group_id",
            "primary",
            "active",
        ]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(area__normalized_name__icontains=value)
            | Q(area__name__icontains=value)
            | Q(area__city__name__icontains=value)
            | Q(location_group__name__icontains=value)
            | Q(object_id__icontains=value)
            | Q(notes__icontains=value)
        ).distinct()


class LocationMatchIgnorePhraseFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")
    phrase_type = django_filters.CharFilter(field_name="phrase_type")
    active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = LocationMatchIgnorePhrase
        fields = ["q", "phrase_type", "active"]

    def filter_q(self, queryset, name, value):
        value = normalize_location_name(value)
        return queryset.filter(
            Q(normalized_phrase__icontains=value)
            | Q(phrase__icontains=value)
        )
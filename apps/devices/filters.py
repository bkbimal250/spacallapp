from django_filters import rest_framework as filters
from django.db.models import Q
from apps.common.filters import BaseDateFilter
from .models import Device

class DeviceFilter(BaseDateFilter):
    search = filters.CharFilter(method='filter_search', label="Search by device ID or token")
    branch = filters.UUIDFilter(field_name='branch_id')
    city = filters.CharFilter(field_name='branch__city', lookup_expr='icontains')
    area = filters.CharFilter(field_name='branch__area', lookup_expr='icontains')
    state = filters.CharFilter(field_name='branch__state', lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_blocked = filters.BooleanFilter()

    class Meta:
        model = Device
        fields = ['branch', 'is_registered', 'is_active', 'is_blocked']
        date_field = 'created_at'

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(device_id__icontains=value) |
            Q(registration_token__icontains=value)
        )

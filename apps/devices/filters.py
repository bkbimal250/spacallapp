from django_filters import rest_framework as filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from apps.common.filters import BaseDateFilter
from .models import Device

class DeviceFilter(BaseDateFilter):
    search = filters.CharFilter(
        method='filter_search',
        label="Search by device, phone, branch, city, area, spa code, Android ID, or token",
    )
    branch = filters.UUIDFilter(field_name='branch_id')
    city = filters.CharFilter(field_name='branch__city', lookup_expr='icontains')
    area = filters.CharFilter(field_name='branch__area', lookup_expr='icontains')
    state = filters.CharFilter(field_name='branch__state', lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_blocked = filters.BooleanFilter()
    is_online = filters.BooleanFilter(method='filter_is_online')

    class Meta:
        model = Device
        fields = ['branch', 'is_registered', 'is_active', 'is_blocked', 'is_online']
        date_field = 'created_at'

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(device_id__icontains=value) |
            Q(phone_name__icontains=value) |
            Q(android_id__icontains=value) |
            Q(registration_token__icontains=value) |
            Q(sim_1_number__icontains=value) |
            Q(sim_2_number__icontains=value) |
            Q(branch__spa_name__icontains=value) |
            Q(branch__code__icontains=value) |
            Q(branch__city__icontains=value) |
            Q(branch__area__icontains=value) |
            Q(branch__state__icontains=value) |
            Q(branch__address__icontains=value) |
            Q(branch__phone__icontains=value) |
            Q(branch__branch_group__name__icontains=value)
        )

    def filter_is_online(self, queryset, name, value):
        from django.conf import settings
        threshold = timezone.now() - timedelta(minutes=getattr(settings, "MONITORING_OFFLINE_AFTER_MINUTES", 20))
        if value:
            return queryset.filter(last_heartbeat__gte=threshold)
        return queryset.exclude(last_heartbeat__gte=threshold)

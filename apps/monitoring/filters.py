from django_filters import rest_framework as filters
from apps.common.filters import BaseDateFilter
from .models import DeviceEvent

class DeviceEventFilter(BaseDateFilter):
    event_type = filters.CharFilter(field_name='event_type')
    branch = filters.UUIDFilter(field_name='device__branch_id')
    resolved = filters.BooleanFilter(field_name='resolved')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = DeviceEvent
        fields = ['event_type', 'branch', 'resolved', 'search']
        date_field = 'created_at'

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        from django.db.models import Q
        return queryset.filter(
            Q(description__icontains=value) |
            Q(device__device_id__icontains=value) |
            Q(device__phone_name__icontains=value) |
            Q(device__android_id__icontains=value) |
            Q(device__branch__spa_name__icontains=value) |
            Q(device__branch__code__icontains=value) |
            Q(device__branch__city__icontains=value) |
            Q(device__branch__area__icontains=value)
        )

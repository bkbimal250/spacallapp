from django_filters import rest_framework as filters
from apps.common.filters import BaseDateFilter
from .models import DeviceEvent

class DeviceEventFilter(BaseDateFilter):
    event_type = filters.CharFilter(field_name='event_type')
    branch = filters.UUIDFilter(field_name='device__branch_id')
    resolved = filters.BooleanFilter(field_name='resolved')

    class Meta:
        model = DeviceEvent
        fields = ['event_type', 'branch', 'resolved']
        date_field = 'created_at'

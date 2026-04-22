from django_filters import rest_framework as filters
from apps.common.filters import BaseDateFilter
from .models import Notification

class NotificationFilter(BaseDateFilter):
    type = filters.CharFilter(field_name='notification_type')
    branch = filters.UUIDFilter(field_name='device__branch_id')

    class Meta:
        model = Notification
        fields = ['type', 'branch']
        date_field = 'created_at'

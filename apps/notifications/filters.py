from django_filters import rest_framework as filters
from apps.common.filters import BaseDateFilter
from .models import Notification

class NotificationFilter(BaseDateFilter):
    type = filters.CharFilter(field_name='notification_type')
    branch = filters.UUIDFilter(method='filter_branch')

    class Meta:
        model = Notification
        fields = ['type', 'branch']
        date_field = 'created_at'

    def filter_branch(self, queryset, name, value):
        return queryset.filter(
            device__branch_id=value
        ) | queryset.filter(
            user__branch_id=value
        )

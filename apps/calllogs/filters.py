from django_filters import rest_framework as filters
from django.db.models import Q
from apps.common.filters import BaseDateFilter
from .models import CallLog

class CallLogFilter(BaseDateFilter):
    branch_search = filters.CharFilter(method='filter_branch_search')
    city = filters.CharFilter(field_name='branch__city', lookup_expr='icontains')
    status = filters.CharFilter(method='filter_status')
    search = filters.CharFilter(method='filter_search')
    is_unique = filters.BooleanFilter(method='filter_is_unique')
    branch = filters.UUIDFilter(field_name='branch_id')
    device = filters.CharFilter(field_name='device__device_id')
    call_type = filters.ChoiceFilter(choices=[
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
    ])

    lead_status = filters.CharFilter(field_name='lead__status')
    sla_status = filters.CharFilter(field_name='followup_status__sla_status')
    branch_group = filters.UUIDFilter(field_name='branch__branch_group_id')

    class Meta:
        model = CallLog
        fields = ['branch', 'device', 'call_type', 'city', 'lead_status', 'sla_status', 'branch_group']
        date_field = 'call_time'

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(phone_number__icontains=value) |
                Q(contact__name__icontains=value)
            )
        return queryset

    def filter_branch_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(branch__spa_name__icontains=value) |
                Q(branch__code__icontains=value)
            )
        return queryset

    def filter_status(self, queryset, name, value):
        if value == 'active':
            return queryset.filter(branch__is_active=True)
        elif value == 'inactive':
            return queryset.filter(branch__is_active=False)
        return queryset

    def filter_is_unique(self, queryset, name, value):
        if value:
            # We use the existing subquery approach for best compatibility with PostgreSQL and DRF pagination
            latest_ids = queryset.order_by('phone_number', '-call_time').distinct('phone_number').values_list('id', flat=True)
            return queryset.filter(id__in=latest_ids).order_by('-call_time')
        return queryset

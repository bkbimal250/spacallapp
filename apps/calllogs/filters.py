from django_filters import rest_framework as filters
from django.db.models import Q
from django.core.exceptions import ValidationError
from apps.common.filters import BaseDateFilter
from .models import CallLog

class CallLogFilter(BaseDateFilter):
    branch_search = filters.CharFilter(method='filter_branch_search')
    city = filters.CharFilter(field_name='branch__city', lookup_expr='icontains')
    status = filters.CharFilter(method='filter_status')
    search = filters.CharFilter(method='filter_search')
    is_unique = filters.BooleanFilter(method='filter_is_unique')
    branch = filters.CharFilter(method='filter_branch')
    device = filters.CharFilter(field_name='device__device_id')
    sim_number = filters.CharFilter(method='filter_sim_number')
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
        fields = ['branch', 'device', 'sim_number', 'call_type', 'city', 'lead_status', 'sla_status', 'branch_group']
        date_field = 'call_time'

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(phone_number__icontains=value) |
                Q(contact__name__icontains=value) |
                Q(device__phone_name__icontains=value) |
                Q(device__device_id__icontains=value) |
                Q(device__sim_1_number__icontains=value) |
                Q(device__sim_2_number__icontains=value)
            )
        return queryset

    def filter_sim_number(self, queryset, name, value):
        if not value:
            return queryset

        normalized = str(value).strip()
        return queryset.filter(
            Q(sim_slot=1, device__sim_1_number=normalized) |
            Q(sim_slot=2, device__sim_2_number=normalized)
        )

    def filter_branch(self, queryset, name, value):
        if not value:
            return queryset

        branch_ids = [item.strip() for item in str(value).split(',') if item.strip()]
        if not branch_ids:
            return queryset

        try:
            return queryset.filter(branch_id__in=branch_ids)
        except ValidationError:
            return queryset.none()

    def filter_branch_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(branch__spa_name__icontains=value) |
                Q(branch__code__icontains=value) |
                Q(branch__city__icontains=value) |
                Q(branch__area__icontains=value) |
                Q(branch__state__icontains=value) |
                Q(branch__address__icontains=value) |
                Q(branch__phone__icontains=value) |
                Q(branch__branch_group__name__icontains=value)
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

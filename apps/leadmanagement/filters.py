from django_filters import rest_framework as filters
from django.db.models import Q
from apps.common.filters import BaseDateFilter
from .models import LeadManagement

class LeadFilter(BaseDateFilter):
    status = filters.CharFilter(lookup_expr='exact')
    branch = filters.UUIDFilter(field_name='branch_id')
    search = filters.CharFilter(method='filter_search')
    
    # For branch summary or list
    branch_search = filters.CharFilter(method='filter_branch_search')
    city = filters.CharFilter(field_name='branch__city', lookup_expr='icontains')
    branch_status = filters.CharFilter(method='filter_branch_status')

    class Meta:
        model = LeadManagement
        fields = ['status', 'branch', 'city']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(calllog__phone_number__icontains=value) |
            Q(remarks__icontains=value) |
            Q(contact__name__icontains=value)
        )

    def filter_branch_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(branch__spa_name__icontains=value) |
            Q(branch__code__icontains=value)
        )

    def filter_branch_status(self, queryset, name, value):
        if value == 'active':
            return queryset.filter(branch__is_active=True)
        elif value == 'inactive':
            return queryset.filter(branch__is_active=False)
        return queryset

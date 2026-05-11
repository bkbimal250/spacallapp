from django_filters import rest_framework as filters
from django.db.models import Q
from apps.common.filters import BaseDateFilter
from .models import Branch, BranchGroups

class BranchFilter(BaseDateFilter):
    """
    Advanced filtering for Branches.
    Supports:
        ?search=<spa_name_or_code>
        ?city=<city>
        ?state=<state>
        ?status=true|false
        ?group=<group_uuid>
        ?quick_date=...
    """
    search = filters.CharFilter(method='filter_search')
    city = filters.CharFilter(lookup_expr='icontains')
    state = filters.CharFilter(lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='is_active')
    branch_group = filters.UUIDFilter(field_name='branch_group_id')

    class Meta:
        model = Branch
        fields = ['search', 'city', 'state', 'status', 'branch_group']
        date_field = 'created_at'

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(spa_name__icontains=value) |
            Q(code__icontains=value)
        )

class BranchGroupFilter(BaseDateFilter):
    """
    Advanced filtering for Branch Groups.
    Supports:
        ?search=<name>
        ?status=true|false
    """
    search = filters.CharFilter(field_name='name', lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = BranchGroups
        fields = ['search', 'status']
        date_field = 'created_at'

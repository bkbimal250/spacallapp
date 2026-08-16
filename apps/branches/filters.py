from django_filters import rest_framework as filters
from django.db.models import Q
from apps.common.filters import BaseDateFilter
from .models import Branch, BranchGroups

class BranchFilter(BaseDateFilter):
    """
    Advanced filtering for Branches.
    Supports:
        ?search=<spa_name_city_area_code>
        ?city=<city>
        ?state=<state>
        ?area=<area>
        ?status=true|false
        ?group=<group_uuid>
        ?open_24_hours=true|false
        ?quick_date=...
    """
    search = filters.CharFilter(method='filter_search')
    city = filters.CharFilter(lookup_expr='icontains')
    state = filters.CharFilter(lookup_expr='icontains')
    area = filters.CharFilter(lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='is_active')
    branch_group = filters.UUIDFilter(field_name='branch_group_id')
    group = filters.UUIDFilter(field_name='branch_group_id')
    open_24_hours = filters.BooleanFilter(method='filter_open_24_hours')
    is_24_hours = filters.BooleanFilter(method='filter_open_24_hours')

    class Meta:
        model = Branch
        fields = ['search', 'city', 'state', 'area', 'status', 'branch_group', 'group', 'open_24_hours', 'is_24_hours']
        date_field = 'created_at'

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(spa_name__icontains=value) |
            Q(code__icontains=value) |
            Q(city__icontains=value) |
            Q(area__icontains=value) |
            Q(state__icontains=value) |
            Q(address__icontains=value) |
            Q(phone__icontains=value) |
            Q(shared_link__icontains=value) |
            Q(branch_group__name__icontains=value)
        )

    def filter_open_24_hours(self, queryset, name, value):
        lookup = {
            "operating_hours__is_active": True,
            "operating_hours__is_deleted": False,
            "operating_hours__is_closed": False,
            "operating_hours__is_24_hours": True,
        }
        if value:
            return queryset.filter(**lookup).distinct()
        return queryset.exclude(**lookup).distinct()

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

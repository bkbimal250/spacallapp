import django_filters

from .models import DoubleTickLead


class DoubleTickLeadFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    branch = django_filters.UUIDFilter(field_name="assigned_branch_id")
    user = django_filters.UUIDFilter(field_name="assigned_user_id")
    device = django_filters.UUIDFilter(field_name="assigned_device_id")

    class Meta:
        model = DoubleTickLead
        fields = [
            "status",
            "city",
            "area",
            "assigned_branch",
            "assigned_user",
            "assigned_device",
            "is_duplicate",
        ]

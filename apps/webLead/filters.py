from django.db.models import Q
from django_filters import rest_framework as filters

from apps.common.filters import BaseDateFilter

from .models import WebsiteFormConfiguration, WebsiteLead


class WebsiteFormConfigurationFilter(BaseDateFilter):
    branch = filters.UUIDFilter(field_name="branch_id")
    website_name = filters.CharFilter(lookup_expr="icontains")
    website_url = filters.CharFilter(lookup_expr="icontains")
    form_key = filters.CharFilter(lookup_expr="iexact")
    is_active = filters.BooleanFilter()
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = WebsiteFormConfiguration
        fields = ["branch", "website_name", "website_url", "form_key", "is_active"]
        date_field = "created_at"

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(website_name__icontains=value)
            | Q(website_url__icontains=value)
            | Q(form_key__icontains=value)
            | Q(branch__spa_name__icontains=value)
        )


class WebsiteLeadFilter(BaseDateFilter):
    branch = filters.UUIDFilter(field_name="branch_id")
    website_name = filters.CharFilter(lookup_expr="icontains")
    website_url = filters.CharFilter(lookup_expr="icontains")
    form_key = filters.CharFilter(lookup_expr="iexact")
    status = filters.CharFilter(lookup_expr="exact")
    routing_status = filters.CharFilter(lookup_expr="exact")
    notification_status = filters.CharFilter(lookup_expr="exact")
    assigned_to = filters.UUIDFilter(field_name="assigned_to_id")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = WebsiteLead
        fields = [
            "branch",
            "website_name",
            "website_url",
            "form_key",
            "status",
            "routing_status",
            "notification_status",
            "assigned_to",
        ]
        date_field = "created_at"

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(customer_name__icontains=value)
            | Q(phone__icontains=value)
            | Q(address__icontains=value)
            | Q(website_name__icontains=value)
            | Q(form_key__icontains=value)
        )

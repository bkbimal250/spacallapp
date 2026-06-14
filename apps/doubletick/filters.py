import django_filters

from .models import DoubleTickConversation, DoubleTickLead


class DoubleTickConversationFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    last_customer_reply_from = django_filters.DateFilter(field_name="last_customer_message_at", lookup_expr="date__gte")
    last_customer_reply_to = django_filters.DateFilter(field_name="last_customer_message_at", lookup_expr="date__lte")
    phone_number = django_filters.CharFilter(field_name="customer__phone_number", lookup_expr="icontains")
    waba_number = django_filters.CharFilter(field_name="channel__waba_number", lookup_expr="icontains")
    has_unread_messages = django_filters.BooleanFilter(method="filter_has_unread")
    is_unmatched = django_filters.BooleanFilter(method="filter_unmatched")

    class Meta:
        model = DoubleTickConversation
        fields = [
            "status",
            "pending_reason",
            "requires_manual_attention",
            "assigned_support_user",
            "channel",
            "customer",
            "raw_city",
            "raw_area",
            "matched_area",
            "area_confirmed",
            "bot_completed",
        ]

    def filter_has_unread(self, queryset, name, value):
        return queryset.filter(unread_count__gt=0) if value else queryset.filter(unread_count=0)

    def filter_unmatched(self, queryset, name, value):
        return queryset.filter(status=DoubleTickConversation.Status.AREA_UNMATCHED) if value else queryset.exclude(status=DoubleTickConversation.Status.AREA_UNMATCHED)


class DoubleTickLeadFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    received_from = django_filters.DateFilter(field_name="received_at", lookup_expr="date__gte")
    received_to = django_filters.DateFilter(field_name="received_at", lookup_expr="date__lte")
    claimed_from = django_filters.DateFilter(field_name="claimed_at", lookup_expr="date__gte")
    claimed_to = django_filters.DateFilter(field_name="claimed_at", lookup_expr="date__lte")
    contacted_from = django_filters.DateFilter(field_name="contacted_at", lookup_expr="date__gte")
    contacted_to = django_filters.DateFilter(field_name="contacted_at", lookup_expr="date__lte")
    branch = django_filters.UUIDFilter(field_name="current_branch_id")
    current_user = django_filters.UUIDFilter(field_name="current_user_id")
    available = django_filters.BooleanFilter(method="filter_available")
    claimed = django_filters.BooleanFilter(method="filter_claimed")

    class Meta:
        model = DoubleTickLead
        fields = [
            "status",
            "channel",
            "matched_area",
            "current_branch",
            "current_user",
            "assigned_branch",
            "assigned_user",
            "assigned_device",
            "is_duplicate",
        ]

    def filter_available(self, queryset, name, value):
        return queryset.filter(status=DoubleTickLead.Status.AVAILABLE) if value else queryset.exclude(status=DoubleTickLead.Status.AVAILABLE)

    def filter_claimed(self, queryset, name, value):
        return queryset.filter(status=DoubleTickLead.Status.CLAIMED) if value else queryset.exclude(status=DoubleTickLead.Status.CLAIMED)

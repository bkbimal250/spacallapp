import django_filters
from django.db.models import Q

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
    branch_id = django_filters.UUIDFilter(method="filter_branch")
    spa = django_filters.CharFilter(method="filter_spa")
    area = django_filters.CharFilter(method="filter_area")
    area_id = django_filters.UUIDFilter(field_name="matched_area_id")
    city = django_filters.CharFilter(method="filter_city")
    state = django_filters.CharFilter(method="filter_state")
    group = django_filters.CharFilter(method="filter_group")
    location_group = django_filters.CharFilter(method="filter_group")
    matched_area_name = django_filters.CharFilter(field_name="matched_area__name", lookup_expr="icontains")
    user = django_filters.UUIDFilter(method="filter_user")
    device = django_filters.UUIDFilter(method="filter_device")
    location_status = django_filters.CharFilter(method="filter_location_status")
    pending_reason = django_filters.CharFilter(field_name="conversation__pending_reason")
    requires_manual_attention = django_filters.BooleanFilter(field_name="conversation__requires_manual_attention")
    waba_number = django_filters.CharFilter(field_name="channel__waba_number", lookup_expr="icontains")
    current_user = django_filters.UUIDFilter(field_name="current_user_id")
    available = django_filters.BooleanFilter(method="filter_available")
    claimed = django_filters.BooleanFilter(method="filter_claimed")
    classification = django_filters.CharFilter(method="filter_match_metadata")
    match_method = django_filters.CharFilter(method="filter_match_metadata")
    confidence_min = django_filters.NumberFilter(method="filter_confidence_min")
    confidence_max = django_filters.NumberFilter(method="filter_confidence_max")
    android_visible = django_filters.BooleanFilter(method="filter_android_visible")
    queue = django_filters.CharFilter(method="filter_queue")

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

    def filter_branch(self, queryset, name, value):
        return queryset.filter(
            Q(current_branch_id=value)
            | Q(assigned_branch_id=value)
            | Q(visibilities__branch_id=value)
        ).distinct()

    def filter_spa(self, queryset, name, value):
        return queryset.filter(
            Q(current_branch__spa_name__icontains=value)
            | Q(assigned_branch__spa_name__icontains=value)
            | Q(visibilities__branch__spa_name__icontains=value)
        ).distinct()

    def filter_area(self, queryset, name, value):
        return queryset.filter(
            Q(raw_area__icontains=value)
            | Q(area__icontains=value)
            | Q(matched_area__name__icontains=value)
        ).distinct()

    def filter_city(self, queryset, name, value):
        return queryset.filter(
            Q(raw_city__icontains=value)
            | Q(city__icontains=value)
            | Q(matched_area__city__icontains=value)
        ).distinct()

    def filter_state(self, queryset, name, value):
        return queryset.filter(
            Q(matched_area__state__icontains=value)
            | Q(current_branch__state__icontains=value)
            | Q(assigned_branch__state__icontains=value)
        ).distinct()

    def filter_group(self, queryset, name, value):
        return queryset.filter(raw_payload__location_match__raw_group__icontains=value)

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(current_user_id=value) | Q(assigned_user_id=value) | Q(visibilities__user_id=value)).distinct()

    def filter_device(self, queryset, name, value):
        return queryset.filter(Q(current_device_id=value) | Q(assigned_device_id=value) | Q(visibilities__device_id=value)).distinct()

    def filter_location_status(self, queryset, name, value):
        if value == "matched":
            return queryset.filter(matched_area__isnull=False)
        if value in ["pending", "unmatched"]:
            return queryset.filter(Q(matched_area__isnull=True) | Q(status=DoubleTickLead.Status.UNASSIGNED))
        return queryset

    def filter_match_metadata(self, queryset, name, value):
        lookup = f"conversation__raw_payload__location_match__{name}"
        return queryset.filter(**{lookup: value})

    def filter_confidence_min(self, queryset, name, value):
        return queryset.filter(conversation__raw_payload__location_match__confidence__gte=value)

    def filter_confidence_max(self, queryset, name, value):
        return queryset.filter(conversation__raw_payload__location_match__confidence__lte=value)

    def filter_android_visible(self, queryset, name, value):
        query = Q(visibilities__device__isnull=False, visibilities__is_visible=True)
        return queryset.filter(query).distinct() if value else queryset.exclude(query).distinct()

    def filter_queue(self, queryset, name, value):
        if value == "closed_lost":
            return queryset.filter(status__in=[DoubleTickLead.Status.CLOSED, DoubleTickLead.Status.LOST])
        return queryset

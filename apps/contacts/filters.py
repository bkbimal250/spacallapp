from django_filters import rest_framework as filters
from django.db.models import Q
from apps.common.filters import BaseDateFilter
from .models import Contact

class ContactFilter(BaseDateFilter):
    search = filters.CharFilter(method='filter_search', label="Search by name or phone number")

    class Meta:
        model = Contact
        fields = []
        date_field = 'created_at'

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(phone_number__icontains=value)
        )

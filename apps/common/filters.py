from rest_framework.filters import BaseFilterBackend
from django_filters import rest_framework as filters
from django.utils import timezone
from datetime import datetime, timedelta

class BaseDateFilter(filters.FilterSet):
    """
    Base FilterSet for consistent date range filtering across modules.
    Usage:
        class MyFilter(BaseDateFilter):
            class Meta:
                model = MyModel
                fields = []
                date_field = 'my_date_field'
    """
    quick_date = filters.CharFilter(method='filter_quick_date', label="Preset: today, yesterday")
    start_date = filters.DateFilter(method='filter_start_date', label="Start Date (YYYY-MM-DD)")
    end_date = filters.DateFilter(method='filter_end_date', label="End Date (YYYY-MM-DD)")

    def get_date_field(self):
        return getattr(self.Meta, 'date_field', 'created_at')

    def filter_quick_date(self, queryset, name, value):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_field = self.get_date_field()

        if value == 'today':
            return queryset.filter(**{f"{date_field}__gte": today_start})
        elif value == 'yesterday':
            yesterday_start = today_start - timedelta(days=1)
            return queryset.filter(**{
                f"{date_field}__gte": yesterday_start,
                f"{date_field}__lt": today_start
            })
        return queryset

    def filter_start_date(self, queryset, name, value):
        if value:
            date_field = self.get_date_field()
            start_of_day = datetime.combine(value, datetime.min.time())
            aware_start = timezone.make_aware(start_of_day) if timezone.is_naive(start_of_day) else start_of_day
            return queryset.filter(**{f"{date_field}__gte": aware_start})
        return queryset

    def filter_end_date(self, queryset, name, value):
        if value:
            date_field = self.get_date_field()
            end_of_day = datetime.combine(value, datetime.max.time())
            aware_end = timezone.make_aware(end_of_day) if timezone.is_naive(end_of_day) else end_of_day
            return queryset.filter(**{f"{date_field}__lte": aware_end})
        return queryset

# Keep existing classes for compatibility if needed, though we should migrate away from them
class DateRangeFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        date_field = getattr(view, 'date_field', 'created_at')

        if start_date:
            filter_kwargs = {f"{date_field}__gte": start_date}
            queryset = queryset.filter(**filter_kwargs)
        
        if end_date:
            filter_kwargs = {f"{date_field}__lte": end_date}
            queryset = queryset.filter(**filter_kwargs)
            
        return queryset

class FieldFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_fields = getattr(view, 'filterset_fields', [])
        filter_kwargs = {}
        
        for field in filter_fields:
            value = request.query_params.get(field)
            if value:
                filter_kwargs[field] = value
                
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
            
        return queryset

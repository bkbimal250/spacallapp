from rest_framework.filters import BaseFilterBackend
from django.core.exceptions import ValidationError

class DateRangeFilter(BaseFilterBackend):
    """
    Filter queryset by 'start_date' and 'end_date' query parameters.
    Format: YYYY-MM-DD
    """
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
    """
    Generic exact match filter.
    Set `filterset_fields` in view.
    """
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

from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncHour
from apps.calllogs.models import CallLog

from datetime import datetime

def get_date_range(request):
    time_filter = request.query_params.get('time_filter', 'last_7_days')
    now = timezone.now()
    
    if time_filter == 'custom':
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        try:
            start_date = timezone.make_aware(datetime.strptime(start_str, "%Y-%m-%d")) if start_str else now - timedelta(days=7)
            end_date = timezone.make_aware(datetime.strptime(end_str, "%Y-%m-%d")).replace(hour=23, minute=59, second=59) if end_str else now
            return start_date, end_date
        except (ValueError, TypeError):
            return now - timedelta(days=7), now
            
    end_date = now
    if time_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_filter == 'last_30_days':
        start_date = now - timedelta(days=30)
    elif time_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # 'last_7_days' default
        start_date = now - timedelta(days=7)
        
    return start_date, end_date

class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date, end_date = get_date_range(request)
        branch_id = request.query_params.get('branch')
        
        base_qs = CallLog.objects.filter(call_time__gte=start_date, call_time__lte=end_date)
        if branch_id and branch_id.strip() and branch_id != 'null' and branch_id != 'undefined':
            base_qs = base_qs.filter(branch_id=branch_id)

        # Calculate conversion data
        stats = base_qs.aggregate(
            incoming=Count('id', filter=Q(call_type='incoming')),
            outgoing=Count('id', filter=Q(call_type='outgoing')),
            missed=Count('id', filter=Q(call_type='missed')),
            rejected=Count('id', filter=Q(call_type='rejected'))
        )

        # Format exactly for Recharts conversion graph structure
        conversion_data = [
            {"name": "Incoming", "value": stats['incoming'] or 0},
            {"name": "Outgoing", "value": stats['outgoing'] or 0},
            {"name": "Missed", "value": stats['missed'] or 0},
            {"name": "Rejected", "value": stats['rejected'] or 0},
        ]

        return Response({
            "conversion_rates": conversion_data,
        })

class PeakHoursView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date, end_date = get_date_range(request)
        branch_id = request.query_params.get('branch')

        # Aggregate Peak Hours
        queryset = CallLog.objects.filter(call_time__gte=start_date, call_time__lte=end_date)
        if branch_id and branch_id.strip() and branch_id != 'null' and branch_id != 'undefined':
            queryset = queryset.filter(branch_id=branch_id)
            
        hourly_data = queryset\
            .annotate(hour=TruncHour('call_time'))\
            .values('hour')\
            .annotate(calls=Count('id'))\
            .order_by('hour')

        mock_data = []
        for h in hourly_data:
            dt = h['hour']
            if dt:
                # Platform independent way to format hour without leading zero
                hour_str = dt.strftime('%I%p').lstrip('0')
            else:
                hour_str = "00:00"
                
            mock_data.append({
                "hour": hour_str,
                "calls": h['calls']
            })

        return Response(mock_data)

from .services import AnalyticsService

class AnalyticsStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date, end_date = get_date_range(request)
        branch_id = request.query_params.get('branch')
        if not (branch_id and branch_id.strip() and branch_id != 'null' and branch_id != 'undefined'):
            branch_id = None
            
        metrics = AnalyticsService.get_metrics(branch_id, start_date, end_date)
        return Response(metrics)


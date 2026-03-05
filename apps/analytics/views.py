from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncHour, ExtractHour
from apps.calllogs.models import CallLog

from datetime import datetime

def get_date_range(request):
    time_filter = request.query_params.get('time_filter', 'today')
    now = timezone.localtime(timezone.now())
    
    if time_filter == 'custom':
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        try:
            start_date = timezone.make_aware(datetime.strptime(start_str, "%Y-%m-%d")) if start_str else now - timedelta(days=7)
            end_date = timezone.make_aware(datetime.strptime(end_str, "%Y-%m-%d")).replace(hour=23, minute=59, second=59) if end_str else now
            return start_date, end_date
        except (ValueError, TypeError):
            return now - timedelta(days=7), now
            
    if time_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == 'yesterday':
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == 'last_30_days':
        start_date = now - timedelta(days=30)
        end_date = now
    elif time_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    else:  # 'last_7_days' default
        start_date = now - timedelta(days=7)
        end_date = now
        
    return start_date, end_date

class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date, end_date = get_date_range(request)
        branch_id = request.query_params.get('branch')
        user = request.user
        
        # Enforce branch restriction for branch manager/regional manager
        assigned_branch_ids = []
        if user.is_authenticated:
            if user.role in ['super_admin', 'admin', 'viewer']:
                if user.role == 'viewer' and user.branch:
                    assigned_branch_ids = [str(user.branch.id)]
                else:
                    assigned_branch_ids = [] # Super/Global Admin sees everything
            elif user.role == 'branch_manager' and user.branch:
                assigned_branch_ids = [str(user.branch.id)]
            elif user.role == 'regional_manager':
                assigned_branch_ids = [str(b.id) for b in user.assigned_branches.all()]
                if not assigned_branch_ids and user.branch:
                    assigned_branch_ids = [str(user.branch.id)]

        base_qs = CallLog.objects.filter(call_time__gte=start_date, call_time__lte=end_date)
        
        if assigned_branch_ids:
            base_qs = base_qs.filter(branch_id__in=assigned_branch_ids)
        elif branch_id:
            if branch_id == 'null':
                base_qs = base_qs.filter(branch__isnull=True)
            elif branch_id.strip() and branch_id != 'undefined':
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
        user = request.user

        # Enforce branch restriction for branch manager/regional manager
        assigned_branch_ids = []
        if user.is_authenticated:
            if user.role in ['super_admin', 'admin', 'viewer']:
                if user.role == 'viewer' and user.branch:
                    assigned_branch_ids = [str(user.branch.id)]
                else:
                    assigned_branch_ids = []
            elif user.role == 'branch_manager' and user.branch:
                assigned_branch_ids = [str(user.branch.id)]
            elif user.role == 'regional_manager':
                assigned_branch_ids = [str(b.id) for b in user.assigned_branches.all()]
                if not assigned_branch_ids and user.branch:
                    assigned_branch_ids = [str(user.branch.id)]

        # Aggregate Peak Hours
        queryset = CallLog.objects.filter(call_time__gte=start_date, call_time__lte=end_date)
        
        if assigned_branch_ids:
            queryset = queryset.filter(branch_id__in=assigned_branch_ids)
        elif branch_id:
            if branch_id == 'null':
                queryset = queryset.filter(branch__isnull=True)
            elif branch_id.strip() and branch_id != 'undefined':
                queryset = queryset.filter(branch_id=branch_id)
            
        hourly_data = queryset\
            .annotate(extracted_hour=ExtractHour('call_time'))\
            .values('extracted_hour')\
            .annotate(calls=Count('id'))\
            .order_by('extracted_hour')

        calls_by_hour = {}
        for h in hourly_data:
            if h['extracted_hour'] is not None:
                hour_val = int(h['extracted_hour'])
                calls_by_hour[hour_val] = h['calls']

        mock_data = []
        for hour in range(24):
            if hour == 0:
                hour_str = "12AM"
            elif hour == 12:
                hour_str = "12PM"
            else:
                hour_str = f"{hour % 12}{'AM' if hour < 12 else 'PM'}"
                
            mock_data.append({
                "hour": hour_str,
                "calls": calls_by_hour.get(hour, 0)
            })

        return Response(mock_data)

from .services import AnalyticsService

class AnalyticsStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date, end_date = get_date_range(request)
        branch_id = request.query_params.get('branch')
        user = request.user

        # Enforce branch restriction for branch manager/regional manager
        assigned_branch_ids = []
        if user.is_authenticated:
            if user.role in ['super_admin', 'admin', 'viewer']:
                if user.role == 'viewer' and user.branch:
                    assigned_branch_ids = [str(user.branch.id)]
                else:
                    assigned_branch_ids = []
            elif user.role == 'branch_manager' and user.branch:
                assigned_branch_ids = [str(user.branch.id)]
            elif user.role == 'regional_manager':
                assigned_branch_ids = [str(b.id) for b in user.assigned_branches.all()]
                if not assigned_branch_ids and user.branch:
                    assigned_branch_ids = [str(user.branch.id)]

        if assigned_branch_ids:
             # AnalyticsService needs to handle list of branch_ids
             metrics = AnalyticsService.get_metrics_multi(assigned_branch_ids, start_date, end_date)
        else:
            if not (branch_id and branch_id.strip() and branch_id != 'null' and branch_id != 'undefined'):
                branch_id = None
            metrics = AnalyticsService.get_metrics(branch_id, start_date, end_date)
        return Response(metrics)

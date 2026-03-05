from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.calllogs.models import CallLog
from apps.devices.models import Device
from apps.branches.models import Branch
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        
        from apps.monitoring.models import DeviceHealth
        
        calls_qs = CallLog.objects.all()
        health_qs = DeviceHealth.objects.all()
        branch_qs = Branch.objects.all()
        
        if assigned_branch_ids:
            calls_qs = calls_qs.filter(branch_id__in=assigned_branch_ids)
            health_qs = health_qs.filter(device__branch_id__in=assigned_branch_ids)
            branch_qs = branch_qs.filter(id__in=assigned_branch_ids)

        total_calls = calls_qs.count()
        # Calculate active devices based on health status flag
        active_devices = health_qs.filter(is_online=True).count()
        missed_calls = calls_qs.filter(call_type='missed').count()
        
        # Calculate avg duration
        avg_dur = calls_qs.aggregate(Avg('duration'))['duration__avg']
        if avg_dur:
            minutes = int(avg_dur // 60)
            seconds = int(avg_dur % 60)
            avg_duration_str = f"{minutes}m {seconds}s"
        else:
            avg_duration_str = "0m 0s"

        # Aggregate 7 days chart trends
        last_7_days = timezone.now() - timedelta(days=7)
        daily_trends = calls_qs.filter(call_time__gte=last_7_days) \
            .annotate(date=TruncDate('call_time')) \
            .values('date') \
            .annotate(calls=Count('id')) \
            .order_by('date')
            
        chart_data = []
        for d in daily_trends:
            chart_data.append({
                "name": d['date'].strftime('%a'),
                "calls": d['calls']
            })
            
        # Aggregate Branch Performance records
        performance_branches = branch_qs.annotate(
            total_calls=Count('call_logs'),
            completed_calls=Count('call_logs', filter=Q(call_logs__call_type='incoming') | Q(call_logs__call_type='outgoing'))
        )[:10]  # Just top 10 for dashboard preview
        
        branch_data = []
        for b in performance_branches:
            conv_rate = round((b.completed_calls / b.total_calls * 100) if b.total_calls > 0 else 0)
            branch_data.append({
                "name": b.spa_name,
                "calls": b.total_calls,
                "conversion": conv_rate,
                "status": "Active" if b.is_active else "Inactive"
            })

        data = {
            "total_calls": total_calls,
            "active_devices": active_devices,
            "missed_calls": missed_calls,
            "avg_duration": avg_duration_str,
            "call_volume_trends": chart_data,
            "branch_performance": branch_data
        }
        return Response(data)


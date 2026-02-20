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
        total_calls = CallLog.objects.count()
        # Calculate active devices (online within last 5 minutes)
        threshold = timezone.now() - timedelta(minutes=5)
        active_devices = Device.objects.filter(last_heartbeat__gte=threshold).count()
        missed_calls = CallLog.objects.filter(call_type='missed').count()
        
        # Calculate avg duration
        avg_dur = CallLog.objects.aggregate(Avg('duration'))['duration__avg']
        if avg_dur:
            minutes = int(avg_dur // 60)
            seconds = int(avg_dur % 60)
            avg_duration_str = f"{minutes}m {seconds}s"
        else:
            avg_duration_str = "0m 0s"

        # Aggregate 7 days chart trends
        last_7_days = timezone.now() - timedelta(days=7)
        daily_trends = CallLog.objects.filter(call_time__gte=last_7_days) \
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
        branches = Branch.objects.annotate(
            total_calls=Count('call_logs'),
            completed_calls=Count('call_logs', filter=Q(call_logs__call_type='incoming') | Q(call_logs__call_type='outgoing'))
        )[:10]  # Just top 10 for dashboard preview
        
        branch_data = []
        for b in branches:
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

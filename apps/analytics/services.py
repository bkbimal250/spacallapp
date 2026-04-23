from django.db.models import Count, Q, Avg, F, Sum
from django.db.models.functions import ExtractHour, TruncDate
from apps.calllogs.models import CallLog
from apps.leadmanagement.models import LeadManagement


class AnalyticsService:
    @staticmethod
    def get_peak_hours(branch_id, date_start, date_end, call_type=None):
        """
        Identify peak calling hours
        """
        queryset = CallLog.objects.filter(call_time__range=(date_start, date_end))
        if branch_id:
            if branch_id == 'null':
                queryset = queryset.filter(branch__isnull=True)
            else:
                queryset = queryset.filter(branch_id=branch_id)
        
        if call_type:
            queryset = queryset.filter(call_type=call_type.lower())
            
        return (
            queryset
            .annotate(hour=ExtractHour("call_time"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

    @staticmethod
    def get_metrics(branch_id, date_start, date_end):
        """
        Calculate missed call ratio and conversion rate proxy (calls > 60s)
        """
        queryset = CallLog.objects.filter(call_time__range=(date_start, date_end))
        if branch_id:
            if branch_id == 'null':
                queryset = queryset.filter(branch__isnull=True)
            else:
                queryset = queryset.filter(branch_id=branch_id)

        stats = queryset.aggregate(
            total_calls=Count("id"),
            missed_calls=Count("id", filter=Q(call_type="missed") | Q(call_type="rejected")),
            converted_calls=Count("id", filter=Q(duration__gte=60, call_type="incoming")),
            avg_duration=Avg("duration")
        )

        total = stats["total_calls"] or 1
        missed_ratio = (stats["missed_calls"] / total) * 100
        conversion_rate = (stats["converted_calls"] / total) * 100
        
        # Simple performance score: 100 - missed_ratio (penalty) + (conversion_rate / 2) (bonus)
        performance_score = max(0, min(100, 100 - missed_ratio + (conversion_rate * 0.5)))

        return {
            "missed_call_ratio": round(missed_ratio, 2),
            "conversion_rate": round(conversion_rate, 2),
            "avg_duration": round(stats["avg_duration"] or 0, 2),
            "performance_score": round(performance_score, 2),
        }
    @staticmethod
    def get_metrics_multi(branch_ids, date_start, date_end):
        """
        Calculate metrics for multiple branches
        """
        queryset = CallLog.objects.filter(call_time__range=(date_start, date_end))
        if branch_ids:
            queryset = queryset.filter(branch_id__in=branch_ids)

        stats = queryset.aggregate(
            total_calls=Count("id"),
            missed_calls=Count("id", filter=Q(call_type="missed") | Q(call_type="rejected")),
            converted_calls=Count("id", filter=Q(duration__gte=60, call_type="incoming")),
            avg_duration=Avg("duration")
        )

        total = stats["total_calls"] or 1
        missed_ratio = (stats["missed_calls"] / total) * 100
        conversion_rate = (stats["converted_calls"] / total) * 100
        
        performance_score = max(0, min(100, 100 - missed_ratio + (conversion_rate * 0.5)))

        return {
            "missed_call_ratio": round(missed_ratio, 2),
            "conversion_rate": round(conversion_rate, 2),
            "avg_duration": round(stats["avg_duration"] or 0, 2),
            "performance_score": round(performance_score, 2),
        }
    @staticmethod
    def get_call_analytics(branch_ids, date_start, date_end, call_type=None):
        """
        Detailed call analytics: volume trends and call type performance.
        """
        queryset = CallLog.objects.filter(call_time__range=(date_start, date_end))
        if branch_ids:
            queryset = queryset.filter(branch_id__in=branch_ids)

        if call_type:
            queryset = queryset.filter(call_type=call_type.lower())

        # 1. Volume Trends (Calls per Day)
        trends = (
            queryset.annotate(date=TruncDate('call_time'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # 2. Daily Metrics Breakdown
        daily_breakdown = (
            queryset.annotate(date=TruncDate('call_time'))
            .values('date')
            .annotate(
                incoming=Count('id', filter=Q(call_type='incoming')),
                outgoing=Count('id', filter=Q(call_type='outgoing')),
                missed=Count('id', filter=Q(call_type='missed')),
            )
            .order_by('date')
        )

        return {
            "trends": list(trends),
            "daily_breakdown": list(daily_breakdown)
        }

    @staticmethod
    def get_lead_analytics(branch_ids, date_start, date_end):
        """
        Lead conversion and status tracking.
        """
        queryset = LeadManagement.objects.filter(created_at__range=(date_start, date_end))
        if branch_ids:
            queryset = queryset.filter(branch_id__in=branch_ids)

        # 1. Status Distribution
        status_counts = queryset.values('status').annotate(count=Count('id'))

        # 2. Conversion Funnel (Manual ordering for visualization)
        # Expected statuses: pending -> ringing -> interested -> coming
        funnel_stats = queryset.aggregate(
            total=Count('id'),
            contacted=Count('id', filter=~Q(status='pending')),
            interested=Count('id', filter=Q(status__in=['interested', 'coming'])),
            bookings=Count('id', filter=Q(status='coming')),
        )

        # 3. Success Metrics
        total = funnel_stats['total'] or 1
        conversion_rate = (funnel_stats['bookings'] / total) * 100
        interest_rate = (funnel_stats['interested'] / total) * 100

        return {
            "status_distribution": list(status_counts),
            "funnel": {
                "Total Leads": funnel_stats['total'],
                "Followed Up": funnel_stats['contacted'],
                "Interested": funnel_stats['interested'],
                "Confirmed Visits": funnel_stats['bookings']
            },
            "rates": {
                "conversion_rate": round(conversion_rate, 2),
                "interest_rate": round(interest_rate, 2)
            }
        }

from django.db.models import Count, Q, Avg, F
from django.db.models.functions import ExtractHour
from apps.calllogs.models import CallLog


class AnalyticsService:
    @staticmethod
    def get_peak_hours(branch_id, date_start, date_end):
        """
        Identify peak calling hours
        """
        return (
            CallLog.objects.filter(
                branch_id=branch_id,
                call_time__range=(date_start, date_end)
            )
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
        stats = CallLog.objects.filter(
            branch_id=branch_id,
            call_time__range=(date_start, date_end)
        ).aggregate(
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

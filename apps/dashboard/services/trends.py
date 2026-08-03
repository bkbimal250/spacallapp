from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_dashboard_querysets, normalize_params


class DashboardTrendService:
    cache_timeout = 60

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("trends", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @classmethod
    def _calculate(cls, user, params, request=None):
        with profile_segment("dashboard.trends", request):
            calls_qs = build_dashboard_querysets(user, params)["calls"]
            last_7_days = timezone.now() - timedelta(days=7)
            daily_trends = (
                calls_qs.filter(call_time__gte=last_7_days)
                .annotate(date=TruncDate("call_time"))
                .values("date")
                .annotate(
                    calls=Count("id"),
                    incoming=Count("id", filter=Q(call_type="incoming")),
                    outgoing=Count("id", filter=Q(call_type="outgoing")),
                    missed=Count("id", filter=Q(call_type="missed")),
                )
                .order_by("date")
            )

            return [
                {
                    "name": item["date"].strftime("%a"),
                    "date": item["date"].isoformat(),
                    "calls": item["calls"],
                    "incoming": item["incoming"],
                    "outgoing": item["outgoing"],
                    "missed": item["missed"],
                }
                for item in daily_trends
            ]

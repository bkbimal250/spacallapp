from django.db.models import Count

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_dashboard_querysets, normalize_params


class DashboardExportService:
    cache_timeout = 60

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("exports", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @classmethod
    def _calculate(cls, user, params, request=None):
        with profile_segment("dashboard.exports", request):
            export_qs = build_dashboard_querysets(user, params)["exports"]
            status_counts = {
                item["status"]: item["count"]
                for item in export_qs.values("status").annotate(count=Count("id"))
            }
            return {
                "total_exports": export_qs.count(),
                "pending_exports": status_counts.get("pending", 0),
                "processing_exports": status_counts.get("processing", 0),
                "completed_exports": status_counts.get("completed", 0),
                "failed_exports": status_counts.get("failed", 0),
                "status_counts": status_counts,
            }

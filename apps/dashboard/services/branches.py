from django.db.models import Count, Q

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_date_filter, build_dashboard_querysets, normalize_params


class DashboardBranchService:
    cache_timeout = 60

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("branches", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @classmethod
    def _calculate(cls, user, params, request=None):
        with profile_segment("dashboard.branches", request):
            branch_qs = build_dashboard_querysets(user, params)["branches"]
            performance_filter = Q()
            lead_source = params.get("lead_source")

            if lead_source == "direct":
                performance_filter &= Q(call_logs__lead__isnull=False)
            elif lead_source == "manual":
                performance_filter &= Q(call_logs__id__isnull=True)

            params = {
                **params,
                "quick_date": params.get("quick_date") or "today",
            }
            performance_filter &= build_date_filter(params, field="call_logs__call_time")
            limit = cls._limit(params)

            rows = (
                branch_qs.annotate(
                    total_calls_count=Count("call_logs", filter=performance_filter),
                    incoming_count=Count("call_logs", filter=performance_filter & Q(call_logs__call_type="incoming")),
                    outgoing_count=Count("call_logs", filter=performance_filter & Q(call_logs__call_type="outgoing")),
                    missed_count=Count("call_logs", filter=performance_filter & Q(call_logs__call_type="missed")),
                    completed_calls_count=Count(
                        "call_logs",
                        filter=performance_filter
                        & (Q(call_logs__call_type="incoming") | Q(call_logs__call_type="outgoing")),
                    ),
                )
                .only("id", "spa_name", "code", "city", "area", "state", "is_active")
                .order_by("-total_calls_count", "spa_name")[:limit]
            )

            data = []
            for branch in rows:
                conversion = round(
                    (branch.completed_calls_count / branch.total_calls_count * 100)
                    if branch.total_calls_count
                    else 0
                )
                data.append(
                    {
                        "id": str(branch.id),
                        "name": branch.spa_name,
                        "code": branch.code,
                        "city": branch.city,
                        "area": branch.area,
                        "state": branch.state,
                        "calls": branch.total_calls_count,
                        "incoming": branch.incoming_count,
                        "outgoing": branch.outgoing_count,
                        "missed": branch.missed_count,
                        "conversion": conversion,
                        "status": "Active" if branch.is_active else "Inactive",
                    }
                )
            return data

    @staticmethod
    def _limit(params):
        try:
            return max(1, min(int(params.get("limit") or params.get("branch_limit") or 20), 20))
        except (TypeError, ValueError):
            return 20

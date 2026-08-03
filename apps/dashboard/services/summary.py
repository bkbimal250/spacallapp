from django.db.models import Avg, Count, Q

from apps.branches.models import Branch
from apps.common.feature_flags import background_analytics_enabled
from apps.common.utils import get_branch_filter_ids

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_dashboard_querysets, normalize_params, today_calls_queryset
from .statistics import DashboardStatisticsService


class DashboardSummaryService:
    cache_timeout = 45

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("summary", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @staticmethod
    def _format_duration(seconds):
        if not seconds:
            return "0m 0s"
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"

    @classmethod
    def _calculate(cls, user, params, request=None):
        statistics_payload = cls._from_statistics_if_possible(user, params)
        if statistics_payload is not None:
            return statistics_payload

        with profile_segment("dashboard.summary", request):
            querysets = build_dashboard_querysets(user, params)
            calls_qs = querysets["calls"]
            today_qs = today_calls_queryset(user, params)

            call_stats = calls_qs.aggregate(
                total_calls=Count("id"),
                missed_calls=Count("id", filter=Q(call_type="missed")),
                avg_duration=Avg("duration"),
            )
            today_stats = today_qs.aggregate(
                today_total_calls=Count("id"),
                today_incoming_calls=Count("id", filter=Q(call_type="incoming")),
                today_outgoing_calls=Count("id", filter=Q(call_type="outgoing")),
                today_missed_calls=Count("id", filter=Q(call_type="missed")),
            )

            return {
                "total_calls": call_stats["total_calls"] or 0,
                "active_devices": querysets["health"].filter(is_online=True).count(),
                "total_devices": querysets["devices"].count(),
                "missed_calls": call_stats["missed_calls"] or 0,
                "total_leads": querysets["leads"].count(),
                "total_branches": querysets["branches"].count(),
                "total_contacts": querysets["contacts"].count(),
                "total_users": querysets["users"].count(),
                "total_exports": querysets["exports"].count(),
                "today_total_calls": today_stats["today_total_calls"] or 0,
                "today_incoming_calls": today_stats["today_incoming_calls"] or 0,
                "today_outgoing_calls": today_stats["today_outgoing_calls"] or 0,
                "today_missed_calls": today_stats["today_missed_calls"] or 0,
                "avg_duration": cls._format_duration(call_stats["avg_duration"]),
            }

    @classmethod
    def _from_statistics_if_possible(cls, user, params):
        if not background_analytics_enabled():
            return None
        if params.get("lead_source") or params.get("start_date") or params.get("end_date"):
            return None
        if params.get("quick_date") not in (None, "", "today"):
            return None

        branch_ids = get_branch_filter_ids(user)
        if branch_ids == ["NONE"]:
            return {
                "total_calls": 0,
                "active_devices": 0,
                "total_devices": 0,
                "missed_calls": 0,
                "total_leads": 0,
                "total_branches": 0,
                "total_contacts": 0,
                "total_users": 0,
                "total_exports": 0,
                "today_total_calls": 0,
                "today_incoming_calls": 0,
                "today_outgoing_calls": 0,
                "today_missed_calls": 0,
                "avg_duration": "0m 0s",
            }

        requested_branch = params.get("branch")
        branch_group = params.get("branch_group")
        effective_branch_ids = branch_ids

        if requested_branch and requested_branch not in ("undefined", "null"):
            effective_branch_ids = [requested_branch]
        elif branch_group and branch_group not in ("undefined", "null"):
            effective_branch_ids = list(
                Branch.objects.filter(branch_group_id=branch_group, is_active=True, is_deleted=False)
                .values_list("id", flat=True)
            )

        stats = DashboardStatisticsService.aggregate_for_branches(effective_branch_ids)
        total_calls = stats["total_calls"]
        return {
            "total_calls": total_calls,
            "active_devices": stats["active_devices"],
            "total_devices": stats["total_devices"],
            "missed_calls": stats["today_missed_calls"],
            "total_leads": stats["total_leads"],
            "total_branches": len(effective_branch_ids) if effective_branch_ids else Branch.objects.filter(is_active=True, is_deleted=False).count(),
            "total_contacts": stats["total_contacts"],
            "total_users": stats["total_users"],
            "total_exports": stats["total_exports"],
            "today_total_calls": total_calls,
            "today_incoming_calls": stats["today_incoming_calls"],
            "today_outgoing_calls": stats["today_outgoing_calls"],
            "today_missed_calls": stats["today_missed_calls"],
            "avg_duration": cls._format_duration(stats["avg_duration"]),
        }

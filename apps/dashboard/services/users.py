from django.db.models import Count

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_dashboard_querysets, normalize_params


class DashboardUserService:
    cache_timeout = 60

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("users", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @classmethod
    def _calculate(cls, user, params, request=None):
        with profile_segment("dashboard.users", request):
            user_qs = build_dashboard_querysets(user, params)["users"]
            role_counts = {item["role"]: item["count"] for item in user_qs.values("role").annotate(count=Count("id"))}
            return {
                "total_users": user_qs.count(),
                "online_users": user_qs.filter(is_online=True).count(),
                "admin_users": role_counts.get("admin", 0) + role_counts.get("super_admin", 0),
                "area_manager_users": role_counts.get("area_manager", 0),
                "spa_manager_users": role_counts.get("spa_manager", 0),
                "role_counts": role_counts,
            }

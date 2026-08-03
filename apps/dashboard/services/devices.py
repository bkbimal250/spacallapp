from django.db.models import Count, Q

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_dashboard_querysets, normalize_params


class DashboardDeviceService:
    cache_timeout = 60

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("devices", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @classmethod
    def _calculate(cls, user, params, request=None):
        with profile_segment("dashboard.devices", request):
            querysets = build_dashboard_querysets(user, params)
            device_stats = querysets["devices"].aggregate(
                total=Count("id"),
                registered=Count("id", filter=Q(is_registered=True)),
                unregistered=Count("id", filter=Q(is_registered=False)),
                blocked=Count("id", filter=Q(is_blocked=True)),
                inactive=Count("id", filter=Q(is_active=False)),
            )
            online = querysets["health"].filter(is_online=True).count()
            total = device_stats["total"] or 0
            return {
                "total_devices": total,
                "registered_devices": device_stats["registered"] or 0,
                "unregistered_devices": device_stats["unregistered"] or 0,
                "active_devices": online,
                "offline_devices": max(total - online, 0),
                "blocked_devices": device_stats["blocked"] or 0,
                "inactive_devices": device_stats["inactive"] or 0,
            }

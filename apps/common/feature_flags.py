from django.conf import settings


def flag_enabled(name, default=False):
    return bool(getattr(settings, name, default))


def dashboard_v2_enabled():
    return flag_enabled("ENABLE_DASHBOARD_V2", True)


def redis_cache_enabled():
    return flag_enabled("ENABLE_REDIS_CACHE", True)


def background_analytics_enabled():
    return flag_enabled("ENABLE_BACKGROUND_ANALYTICS", False)


def sql_profiling_enabled():
    return flag_enabled("ENABLE_SQL_PROFILING", False)


def refresh_rotation_enabled():
    return flag_enabled("ENABLE_REFRESH_ROTATION", True)


def device_sessions_enabled():
    return flag_enabled("ENABLE_DEVICE_SESSIONS", True)

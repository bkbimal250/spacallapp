import hashlib
import json
import logging

from django.core.cache import cache
from apps.common.feature_flags import redis_cache_enabled

logger = logging.getLogger(__name__)

DASHBOARD_CACHE_PREFIX = "dashboard"


def make_cache_key(segment, user, params=None):
    role = getattr(user, "role", "anonymous")
    user_id = str(getattr(user, "id", "anonymous"))
    payload = {
        "segment": segment,
        "user": user_id,
        "role": role,
        "params": sorted((params or {}).items()),
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{DASHBOARD_CACHE_PREFIX}:{segment}:{digest}"


def get_or_set(segment, user, params, builder, timeout, request=None):
    if not redis_cache_enabled():
        return builder()

    key = make_cache_key(segment, user, params)
    cached = cache.get(key)
    if cached is not None:
        _record_cache_meta(request, hit=True, key=key)
        return cached

    _record_cache_meta(request, miss=True, key=key)
    data = builder()
    cache.set(key, data, timeout=timeout)
    return data


def _record_cache_meta(request, hit=False, miss=False, key=""):
    if request is None:
        return
    meta = getattr(request, "_dashboard_cache", {"hit": False, "miss": False, "key": ""})
    meta["hit"] = bool(meta.get("hit") or hit)
    meta["miss"] = bool(meta.get("miss") or miss)
    meta["key"] = key or meta.get("key", "")
    request._dashboard_cache = meta


def invalidate_dashboard_cache(*segments):
    if not redis_cache_enabled():
        return

    target_segments = segments or ("summary", "devices", "branches", "trends", "users", "contacts", "exports")
    try:
        for segment in target_segments:
            cache.delete_pattern(f"{DASHBOARD_CACHE_PREFIX}:{segment}:*")
    except AttributeError:
        logger.info("Dashboard cache backend does not support delete_pattern.")
    except Exception:
        logger.exception("Failed to invalidate dashboard cache.")

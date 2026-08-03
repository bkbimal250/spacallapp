import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

logger = logging.getLogger(__name__)

_OBSERVABILITY_TABLES_AVAILABLE = None


class ObservabilityService:
    @staticmethod
    def should_observe_path(path):
        if not getattr(settings, "ENABLE_API_OBSERVABILITY", True):
            return False
        prefixes = getattr(settings, "API_OBSERVABILITY_PATH_PREFIXES", [])
        return any(str(path).startswith(prefix) for prefix in prefixes)

    @staticmethod
    def record_request(request, response, duration_ms, queries, error=""):
        try:
            from .models import APIRequestMetric, SlowQuery

            if not ObservabilityService.tables_available():
                return

            status_code = getattr(response, "status_code", 500)
            slowest_query_ms = 0.0
            slow_queries = []
            threshold_ms = getattr(settings, "API_SLOW_QUERY_THRESHOLD_MS", 500)

            for query in queries:
                query_ms = ObservabilityService._query_time_ms(query)
                slowest_query_ms = max(slowest_query_ms, query_ms)
                if query_ms >= threshold_ms:
                    slow_queries.append((query, query_ms))

            cache_meta = getattr(request, "_dashboard_cache", {})
            metric = APIRequestMetric.objects.create(
                request_id=getattr(request, "request_id", ""),
                method=request.method,
                path=request.path[:500],
                view_name=ObservabilityService._view_name(request),
                status_code=status_code,
                duration_ms=duration_ms,
                sql_count=len(queries),
                slowest_query_ms=round(slowest_query_ms, 2),
                cache_hit=bool(cache_meta.get("hit")),
                cache_miss=bool(cache_meta.get("miss")),
                cache_key=str(cache_meta.get("key") or "")[:255],
                user_id=getattr(getattr(request, "user", None), "id", None),
                error=error,
            )

            SlowQuery.objects.bulk_create(
                [
                    SlowQuery(
                        request_metric=metric,
                        request_id=metric.request_id,
                        path=metric.path,
                        duration_ms=round(query_ms, 2),
                        sql=str(query.get("sql") or "")[:5000],
                    )
                    for query, query_ms in slow_queries
                ],
                ignore_conflicts=True,
            )
        except (OperationalError, ProgrammingError):
            logger.warning("API observability tables are unavailable; skipping metric write.")
        except Exception:
            logger.warning("Failed to persist API observability metric.", exc_info=True)

    @staticmethod
    def platform_summary(minutes=60):
        from django.db.models import Avg, Count, Max, Q
        from .models import APIRequestMetric

        if not ObservabilityService.tables_available():
            return []

        since = timezone.now() - timedelta(minutes=minutes)
        queryset = APIRequestMetric.objects.filter(created_at__gte=since)
        rows = (
            queryset.values("path")
            .annotate(
                request_count=Count("id"),
                error_count=Count("id", filter=Q(status_code__gte=500)),
                avg_ms=Avg("duration_ms"),
                max_ms=Max("duration_ms"),
                avg_sql=Avg("sql_count"),
                cache_hits=Count("id", filter=Q(cache_hit=True)),
                cache_misses=Count("id", filter=Q(cache_miss=True)),
            )
            .order_by("-request_count")[:50]
        )

        return [
            {
                **row,
                "avg_ms": round(row["avg_ms"] or 0, 2),
                "max_ms": round(row["max_ms"] or 0, 2),
                "avg_sql": round(row["avg_sql"] or 0, 2),
                "cache_hit_rate": round(
                    (row["cache_hits"] / max((row["cache_hits"] + row["cache_misses"]), 1)) * 100,
                    2,
                ),
            }
            for row in rows
        ]

    @staticmethod
    def health():
        checks = {
            "database": ObservabilityService._database_ok(),
            "cache": ObservabilityService._cache_ok(),
        }
        overall = "ok" if all(item["ok"] for item in checks.values()) else "degraded"
        return {"status": overall, "checks": checks}

    @staticmethod
    def cleanup_old_metrics():
        from .models import APIRequestMetric, SlowQuery

        if not ObservabilityService.tables_available():
            return

        cutoff = timezone.now() - timedelta(days=getattr(settings, "API_METRIC_RETENTION_DAYS", 14))
        SlowQuery.objects.filter(created_at__lt=cutoff).delete()
        APIRequestMetric.objects.filter(created_at__lt=cutoff).delete()

    @staticmethod
    def tables_available():
        global _OBSERVABILITY_TABLES_AVAILABLE

        if _OBSERVABILITY_TABLES_AVAILABLE is not None:
            return _OBSERVABILITY_TABLES_AVAILABLE

        try:
            table_names = connection.introspection.table_names()
            _OBSERVABILITY_TABLES_AVAILABLE = (
                "api_request_metrics" in table_names
                and "slow_queries" in table_names
            )
        except Exception:
            _OBSERVABILITY_TABLES_AVAILABLE = False

        return _OBSERVABILITY_TABLES_AVAILABLE

    @staticmethod
    def _query_time_ms(query):
        try:
            return float(query.get("time") or 0) * 1000
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _view_name(request):
        resolver_match = getattr(request, "resolver_match", None)
        if not resolver_match:
            return ""
        return resolver_match.view_name or getattr(resolver_match.func, "__name__", "")

    @staticmethod
    def _database_ok():
        start = timezone.now()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            latency_ms = (timezone.now() - start).total_seconds() * 1000
            return {"ok": True, "latency_ms": round(latency_ms, 2)}
        except OperationalError as exc:
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _cache_ok():
        start = timezone.now()
        key = "health:cache"
        try:
            cache.set(key, "ok", timeout=10)
            ok = cache.get(key) == "ok"
            latency_ms = (timezone.now() - start).total_seconds() * 1000
            return {"ok": ok, "latency_ms": round(latency_ms, 2)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

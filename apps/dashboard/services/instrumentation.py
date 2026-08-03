import logging
from contextlib import contextmanager
from time import perf_counter

from django.conf import settings
from django.db import connection, reset_queries

from apps.common.feature_flags import sql_profiling_enabled

logger = logging.getLogger("apps.dashboard.performance")


def _sql_profiling_enabled(request=None):
    if request is not None and request.query_params.get("profile_sql") == "1":
        return True
    return sql_profiling_enabled() or bool(getattr(settings, "DASHBOARD_PROFILE_SQL", False))


@contextmanager
def profile_segment(name, request=None):
    include_sql = _sql_profiling_enabled(request)
    previous_force_debug_cursor = connection.force_debug_cursor

    if include_sql:
        reset_queries()
        connection.force_debug_cursor = True

    start = perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((perf_counter() - start) * 1000, 2)
        queries = list(connection.queries) if include_sql else []

        logger.info(
            "Dashboard segment profiled",
            extra={
                "segment": name,
                "elapsed_ms": elapsed_ms,
                "sql_query_count": len(queries),
                "sql_queries": [
                    {
                        "time": query.get("time"),
                        "sql": query.get("sql"),
                    }
                    for query in queries
                ],
            },
        )

        if include_sql:
            connection.force_debug_cursor = previous_force_debug_cursor

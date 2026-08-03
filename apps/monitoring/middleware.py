import uuid
from time import perf_counter

from django.db import connection, reset_queries

from .services_observability import ObservabilityService


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class APIMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not ObservabilityService.should_observe_path(request.path):
            return self.get_response(request)

        previous_force_debug_cursor = connection.force_debug_cursor
        connection.force_debug_cursor = True
        reset_queries()
        start = perf_counter()
        response = None
        error = ""

        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            error = str(exc)[:1000]
            raise
        finally:
            duration_ms = round((perf_counter() - start) * 1000, 2)
            queries = list(connection.queries)
            connection.force_debug_cursor = previous_force_debug_cursor
            ObservabilityService.record_request(
                request=request,
                response=response,
                duration_ms=duration_ms,
                queries=queries,
                error=error,
            )

import logging
from datetime import timedelta
from apps.common.task_policy import fresh_call, eligible_device
from apps.calllogs.models import CallLog

from django.conf import settings
from django.db import transaction

from apps.callrouting.tasks import process_call_log_routing

logger = logging.getLogger(__name__)


def enqueue_call_log_routing(call_log_ids):
    """
    Queue routing tasks for committed CallLog IDs when routing is enabled.

    Uses one task per CallLog ID to keep Celery payloads small and retries easy
    to inspect. Duplicate task delivery is safe because RoutingService is
    idempotent at the database layer.
    """
    if not getattr(settings, "ENABLE_CALL_ROUTING", False):
        return 0

    ids = [str(call_log_id) for call_log_id in call_log_ids if call_log_id]
    if not ids:
        return 0

    def _enqueue():
        for call in CallLog.objects.filter(id__in=ids).select_related("device"):
            if fresh_call(call, settings.CALL_ROUTING_MAX_AGE_SECONDS) and eligible_device(call):
                process_call_log_routing.apply_async(
                    args=(str(call.id),), ignore_result=True,
                    expires=call.call_time + timedelta(seconds=settings.CALL_ROUTING_MAX_AGE_SECONDS),
                )
        logger.info("Queued call routing tasks", extra={"routing_task_count": len(ids)})

    transaction.on_commit(_enqueue)
    return len(ids)

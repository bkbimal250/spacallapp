"""Execution-time policy shared by producers and consumers (including legacy tasks)."""
from datetime import timedelta

from django.utils import timezone


def fresh_call(call, max_age_seconds, now=None):
    now = now or timezone.now()
    timestamp = call.call_time
    return bool(
        timestamp and timezone.is_aware(timestamp)
        and not call.is_time_invalid
        and not getattr(call, "is_deleted", False)
        and timedelta(0) <= now - timestamp < timedelta(seconds=max_age_seconds)
    )


def eligible_device(call):
    device = call.device
    return bool(device and device.is_active and device.is_registered
                and not device.is_blocked and not getattr(device, "is_deleted", False)
                and device.branch_id == call.branch_id)

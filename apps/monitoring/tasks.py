import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.devices.models import Device
from .models import DeviceHealth
from .services import MonitoringAlertService, offline_threshold
from .compliance import DeviceComplianceService

logger = logging.getLogger(__name__)


@shared_task
def check_offline_devices():
    """
    Mark registered devices offline when heartbeat is stale and notify the
    device, branch manager, area manager, and realtime dashboard.
    """
    threshold = offline_threshold()
    uninstall_threshold = timezone.now() - timedelta(
        hours=getattr(settings, "MONITORING_UNINSTALL_SUSPECT_AFTER_HOURS", 24)
    )

    late_devices = Device.objects.filter(
        is_active=True,
        is_registered=True,
        is_deleted=False,
    ).filter(
        Q(last_heartbeat__lt=threshold) | Q(last_heartbeat__isnull=True)
    ).select_related("branch")

    affected = 0
    for device in late_devices:
        health, _ = DeviceHealth.objects.get_or_create(device=device)
        if health.is_online:
            health.is_online = False
            health.save(update_fields=["is_online", "updated_at"])

        last_seen = device.last_heartbeat.strftime("%Y-%m-%d %H:%M") if device.last_heartbeat else "Never"
        MonitoringAlertService.raise_event(
            device=device,
            event_type="offline",
            description=f"Device went offline. Last seen: {last_seen}",
        )
        if device.last_heartbeat is None or device.last_heartbeat < uninstall_threshold:
            hours = getattr(settings, "MONITORING_UNINSTALL_SUSPECT_AFTER_HOURS", 24)
            MonitoringAlertService.raise_event(
                device=device,
                event_type="app_uninstall_suspected",
                description=(
                    f"No app heartbeat for at least {hours} hours. "
                    "Possible reasons: app uninstalled or force-stopped, phone switched off, "
                    f"or no internet. Last seen: {last_seen}"
                ),
            )
        MonitoringAlertService.broadcast_device_status(device, "offline")
        affected += 1

    return f"Checked offline devices. Affected: {affected}"


@shared_task
def check_device_sync_health():
    """
    Monitor device sync freshness and send realtime alerts.
    Rules:
      - > 2 hours since last sync: reminder alert.
      - > 24 hours since last sync: critical alert.
    """
    now = timezone.now()
    threshold_24h = now - timedelta(hours=24)
    threshold_2h = now - timedelta(hours=2)

    late_24h = DeviceHealth.objects.filter(
        device__is_active=True,
        device__is_registered=True,
        device__is_deleted=False,
        notified_24h=False,
    ).filter(
        Q(last_sync__lt=threshold_24h) |
        Q(last_sync__isnull=True, device__created_at__lt=threshold_24h)
    ).select_related("device", "device__branch")

    critical_count = 0
    for health in late_24h:
        MonitoringAlertService.raise_event(
            device=health.device,
            event_type="sync_failure",
            description="Data has not been synced for 24 hours. Immediate action required.",
        )
        health.notified_24h = True
        health.notified_2h = True
        health.save(update_fields=["notified_24h", "notified_2h", "updated_at"])
        critical_count += 1
        logger.info("Sent 24h critical sync alert to device %s", health.device.device_id)

    late_2h = DeviceHealth.objects.filter(
        device__is_active=True,
        device__is_registered=True,
        device__is_deleted=False,
        notified_2h=False,
    ).filter(
        Q(last_sync__lt=threshold_2h) |
        Q(last_sync__isnull=True, device__created_at__lt=threshold_2h)
    ).select_related("device", "device__branch")

    reminder_count = 0
    for health in late_2h:
        if health.last_sync and health.last_sync < threshold_24h:
            continue

        MonitoringAlertService.raise_event(
            device=health.device,
            event_type="sync_failure",
            description="Your data is not synced. Please refresh or sync the app.",
        )
        health.notified_2h = True
        health.save(update_fields=["notified_2h", "updated_at"])
        reminder_count += 1
        logger.info("Sent 2h sync reminder to device %s", health.device.device_id)

    return f"Checked sync health. Reminders: {reminder_count}, critical: {critical_count}"


@shared_task
def send_device_compliance_alerts():
    from django.core.management import call_command

    call_command("send_device_compliance_alerts", "--commit")

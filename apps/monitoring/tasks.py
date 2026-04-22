from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.devices.models import Device


@shared_task
def check_offline_devices():
    """
    Periodic task to check for devices that have stopped communicating.
    
    If a device has not sent a heartbeat in the last 5 minutes, it is marked
    as offline, and a notification is sent to its branch.
    """
    from apps.monitoring.models import DeviceHealth, DeviceEvent
    from apps.notifications.services import NotificationService
    
    threshold = timezone.now() - timedelta(minutes=5)

    # Find devices that are active but haven't responded within the threshold
    late_devices = Device.objects.filter(
        last_heartbeat__lt=threshold, 
        is_active=True,
        is_deleted=False
    ).select_related('branch')

    for device in late_devices:
        # Update Health status to offline
        health, _ = DeviceHealth.objects.get_or_create(device=device)
        if health.is_online:
            health.is_online = False
            health.save()
            
            # Check if an unresolved offline event already exists to prevent duplicate alerts
            if not DeviceEvent.objects.filter(device=device, event_type='offline', resolved=False).exists():
                last_seen = device.last_heartbeat.strftime('%Y-%m-%d %H:%M') if device.last_heartbeat else "Never"
                description = f"Device went offline. Last seen: {last_seen}"
                
                DeviceEvent.objects.create(
                    device=device,
                    event_type='offline',
                    description=description
                )
                
                # Notify the branch manager/admin via Push Notification
                NotificationService.send_push(
                    device=device,
                    title="Device Stopped Syncing",
                    body=f"Device {device.device_id} at {device.branch.spa_name if device.branch else 'Unknown'} is currently offline.",
                    notification_type="sync_issue"
                )


@shared_task
def check_device_sync_health():
    """
    Task to monitor device sync intervals and send alerts via FCM.
    Rules:
      - > 2 hours since last sync: Send mild reminder.
      - > 24 hours since last sync: Send urgent alert.
    """
    from apps.monitoring.models import DeviceHealth
    from apps.notifications.services import NotificationService
    import logging

    logger = logging.getLogger(__name__)
    now = timezone.now()
    
    threshold_24h = now - timedelta(hours=24)
    threshold_2h = now - timedelta(hours=2)

    # 1. Check for 24-hour sync failures (highest priority)
    late_24h = DeviceHealth.objects.filter(
        device__is_active=True,
        device__is_deleted=False,
        last_sync__lt=threshold_24h,
        notified_24h=False
    ).select_related('device', 'device__branch')

    for health in late_24h:
        success = NotificationService.send_push(
            device=health.device,
            title="⚠️ Sync Required Immediately",
            body="Data has not been synced for 24 hours. Immediate action required.",
            notification_type="sync_issue"
        )
        if success:
            health.notified_24h = True
            health.notified_2h = True  # If 24h is sent, we don't need to send 2h anymore
            health.save(update_fields=["notified_24h", "notified_2h"])
            logger.info(f"Sent 24h critical sync alert to device {health.device.device_id}")

    # 2. Check for 2-hour sync failures
    late_2h = DeviceHealth.objects.filter(
        device__is_active=True,
        device__is_deleted=False,
        last_sync__lt=threshold_2h,
        notified_2h=False
    ).select_related('device', 'device__branch')

    for health in late_2h:
        # Avoid sending 2h if they already crossed 24h (though flags should prevent it)
        if health.last_sync < threshold_24h:
            continue

        success = NotificationService.send_push(
            device=health.device,
            title="Sync Reminder",
            body="Your data is not synced. Please refresh or sync the app.",
            notification_type="reminder"
        )
        if success:
            health.notified_2h = True
            health.save(update_fields=["notified_2h"])
            logger.info(f"Sent 2h sync reminder to device {health.device.device_id}")


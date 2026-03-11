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


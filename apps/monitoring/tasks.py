from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.devices.models import Device


@shared_task
def check_offline_devices():
    from apps.monitoring.models import DeviceHealth, DeviceEvent
    
    threshold = timezone.now() - timedelta(minutes=10)

    # Find devices that have heartbeats but are now late
    late_devices = Device.objects.filter(
        last_heartbeat__lt=threshold, 
        is_active=True
    )

    for device in late_devices:
        # Update Health status
        health, _ = DeviceHealth.objects.get_or_create(device=device)
        if health.is_online:
            health.is_online = False
            health.save()
            
            # Create Event if not already alerted
            if not DeviceEvent.objects.filter(device=device, event_type='offline', resolved=False).exists():
                DeviceEvent.objects.create(
                    device=device,
                    event_type='offline',
                    description=f"Device missed heartbeats since {device.last_heartbeat}"
                )


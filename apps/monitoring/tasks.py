from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.devices.models import Device


@shared_task
def check_offline_devices():

    threshold = timezone.now() - timedelta(minutes=10)

    # Filter devices that haven't sent a heartbeat recently
    devices = Device.objects.filter(last_heartbeat__lt=threshold, is_active=True)

    # Bulk update to mark as inactive or just log? 
    # User request said: devices.update(is_active=False)
    # This might have side effects if is_active prevents login, but it's what was asked.
    devices.update(is_active=False)

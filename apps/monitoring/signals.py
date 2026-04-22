from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.devices.models import Device
from .models import DeviceHealth

@receiver(post_save, sender=Device)
def create_device_health(sender, instance, created, **kwargs):
    """
    Ensure a DeviceHealth record exists for every Device.
    """
    if created:
        DeviceHealth.objects.get_or_create(device=instance)

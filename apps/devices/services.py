from django.utils import timezone
from .models import Device, Lastsynchistory


class DeviceService:

    @staticmethod
    def register_device(data):
        return Device.objects.create(**data)

    @staticmethod
    def update_heartbeat(device):
        device.last_heartbeat = timezone.now()
        device.save(update_fields=["last_heartbeat"])

    @staticmethod
    def update_sync_time(device):
        device.last_sync = timezone.now()
        device.save(update_fields=["last_sync"])
        Lastsynchistory.objects.update_or_create(
            device=device,
            defaults={"last_sync_time": device.last_sync},
        )
        return device.last_sync

    @staticmethod
    def block_device(device):
        device.is_blocked = True
        device.save(update_fields=["is_blocked"])

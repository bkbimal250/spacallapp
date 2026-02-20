from django.utils import timezone
from datetime import timedelta
from apps.devices.models import Device
from .models import DeviceEvent


class MonitoringService:
    @staticmethod
    def check_offline_devices(threshold_minutes=15):
        """
        Identify devices that haven't sent a heartbeat recently
        """
        cutoff = timezone.now() - timedelta(minutes=threshold_minutes)
        offline_devices = Device.objects.filter(
            last_heartbeat__lt=cutoff, is_active=True
        )

        for device in offline_devices:
            # Log event if not already logged recently?
            # For simplicity, we just create an event.
            # In production, check if an open 'offline' event exists.
            exists = DeviceEvent.objects.filter(
                device=device, event_type="offline", resolved=False
            ).exists()
            
            if not exists:
                DeviceEvent.objects.create(
                    device=device,
                    event_type="offline",
                    description=f"Device offline since {device.last_heartbeat}",
                )

    @staticmethod
    def log_sim_change(device, new_sim_1, new_sim_2=None):
        description = f"SIM 1 changed from {device.sim_1_number} to {new_sim_1}"
        if new_sim_2:
            description += f", SIM 2 changed to {new_sim_2}"
            
        DeviceEvent.objects.create(
            device=device,
            event_type="sim_change",
            description=description
        )

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Device


class DeviceAuthentication(BaseAuthentication):

    def authenticate(self, request):

        device_id = request.headers.get("X-Device-ID")
        secret_key = request.headers.get("X-Device-Secret")

        if not device_id or not secret_key:
            return None

        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            raise AuthenticationFailed("Invalid device")

        if device.secret_key != secret_key:
            raise AuthenticationFailed("Invalid device secret")

        if not device.is_active or device.is_blocked:
            raise AuthenticationFailed("Device not allowed")

        # Return (user, auth) tuple. 
        # Since usage of request.user usually implies a User object, 
        # but here we return the Device object as the 'user'.
        return (device, device)


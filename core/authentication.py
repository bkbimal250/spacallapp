print("Loading core.authentication module")
from rest_framework import authentication
from rest_framework import exceptions


class DeviceAuthentication(authentication.BaseAuthentication):
    """
    Authenticate Android devices via X-Device-ID and X-Device-Secret headers.
    """

    def authenticate(self, request):
        from apps.devices.models import Device
        print("DeviceAuthentication.authenticate called")

        print("DeviceAuthentication.authenticate called")
        device_id = request.headers.get("X-Device-ID")
        secret_key = request.headers.get("X-Device-Secret")
        print(f"DeviceID: {device_id}, Match found: {bool(device_id and secret_key)}")

        if not device_id or not secret_key:
            return None

        try:
            device = Device.objects.get(
                device_id=device_id,
                secret_key=secret_key
            )
            print("Device found in DB")
        except Device.DoesNotExist:
            print("Device NOT found in DB")
            raise exceptions.AuthenticationFailed("Invalid Device Credentials")


        if not device.is_active:
            raise exceptions.AuthenticationFailed("Device is inactive")

        if device.is_blocked:
            raise exceptions.AuthenticationFailed("Device is blocked")

        return (device, device)

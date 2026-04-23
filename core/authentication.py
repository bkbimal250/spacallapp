print("Loading core.authentication module")
from rest_framework import authentication
from rest_framework import exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class DeviceAuthentication(authentication.BaseAuthentication):
    """
    Authenticate Android devices via X-Device-ID and X-Device-Secret headers.
    """

    def authenticate(self, request):
        from apps.devices.models import Device
        print("DeviceAuthentication.authenticate called")

        device_id = request.headers.get("X-Device-ID")
        secret_key = request.headers.get("X-Device-Secret")
        
        if not device_id or not secret_key:
            return None

        try:
            device = Device.objects.get(
                device_id=device_id,
                secret_key=secret_key
            )
        except Device.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid Device Credentials")


        if not device.is_active:
            raise exceptions.AuthenticationFailed("Device is inactive")

        if device.is_blocked:
            raise exceptions.AuthenticationFailed("Device is blocked")

        return (device, device)


class DeviceAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = DeviceAuthentication
    name = 'DeviceAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Device-ID',
            'description': 'Device Authentication requires X-Device-ID and X-Device-Secret headers.'
        }

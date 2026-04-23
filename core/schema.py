from drf_spectacular.extensions import OpenApiAuthenticationExtension
from core.authentication import DeviceAuthentication

class DeviceAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = DeviceAuthentication
    name = 'DeviceAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Device-ID',
            'description': 'Device ID header',
        }

    def get_security_requirement(self, auto_schema):
        return {
            'DeviceAuth': [],
            'X-Device-Secret': [] # This is just a hint, we can't easily define two headers in one scheme in standard OpenAPI 3.0 easily without more complex setup, but this registers it.
        }

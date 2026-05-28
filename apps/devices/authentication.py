"""
Compatibility import for device authentication.

The production API imports DeviceAuthentication from core.authentication. This
module keeps older/local imports aligned with the same implementation.
"""

from core.authentication import DeviceAuthentication


__all__ = ["DeviceAuthentication"]

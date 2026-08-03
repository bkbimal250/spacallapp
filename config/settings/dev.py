from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use console backend for development to see OTPs in logs
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Local development should work even when Redis is not running. Production
# settings keep Redis for Channels, Celery, and shared cache behavior.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "calllog-system-dev",
    }
}

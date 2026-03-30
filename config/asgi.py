"""
ASGI config for calllog_system project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# Step 1: Set the default settings module for the 'django' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

# Step 2: Initialize Django application (loads apps, models, etc.)
# This MUST happen BEFORE importing any application parts that access the database or models.
django.setup()

# Step 3: Get the ASGI application for handling HTTP requests.
# This should be defined AFTER django.setup()
django_asgi_app = get_asgi_application()

# Step 4: Import routing and middleware components AFTER django.setup()
# This avoids "AppRegistryNotReady" errors where models are imported before apps are loaded.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.accounts.routing import websocket_urlpatterns
from apps.accounts.middleware import JWTAuthMiddleware

# Step 5: Define the final application as a ProtocolTypeRouter
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})

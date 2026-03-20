from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use console backend for development to see OTPs in logs
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

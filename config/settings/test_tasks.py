"""Offline task tests: deliberately independent of base.py and the root .env."""
import os

# Celery broker environment overrides must not escape this offline profile.
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
SECRET_KEY = "offline-tests-only-not-a-deployment-key"
DEBUG = False
USE_TZ = True
TIME_ZONE = "Asia/Kolkata"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
INSTALLED_APPS = [
    "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "rest_framework", "rest_framework_simplejwt.token_blacklist",
    "core", "apps.accounts", "apps.branches", "apps.devices", "apps.calllogs",
    "apps.common", "apps.monitoring", "apps.analytics", "apps.exports",
    "apps.dashboard", "apps.contacts", "apps.leadmanagement", "apps.callrouting",
    "apps.notifications", "apps.doubletick", "apps.bots", "apps.locations", "apps.webLead",
]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
ENABLE_REDIS_CACHE = False
ENABLE_BACKGROUND_ANALYTICS = False
ENABLE_API_OBSERVABILITY = False
ENABLE_CALL_ROUTING = True
CALL_ROUTING_DRY_RUN = False
ENABLE_CALL_ROUTING_WHATSAPP = True
MISSED_CALL_MAX_AGE_SECONDS = 5400
MISSED_CALL_SWEEP_BATCH_SIZE = 200
MISSED_CALL_QUEUE_LEASE_SECONDS = 300
CALL_ROUTING_MAX_AGE_SECONDS = 5400
SEND_CLAIM_TIMEOUT_SECONDS = 300
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_TASK_DEFAULT_QUEUE = "calllog_offline_test"
CELERY_TASK_ROUTES = ("config.task_routes.route_project_task",)
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_CREATE_MISSING_QUEUES = False
from kombu import Queue
CELERY_TASK_QUEUES = (Queue(CELERY_TASK_DEFAULT_QUEUE),)
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

ROOT_URLCONF = "config.urls"
INSTALLED_APPS += ["django.contrib.admin", "django.contrib.messages", "django.contrib.staticfiles"]
MIDDLEWARE = ["django.contrib.sessions.middleware.SessionMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware"]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
STATIC_URL = "/static/"
ALLOWED_HOSTS = ["testserver", "localhost"]
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["core.authentication.SessionAwareJWTAuthentication"], "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsSetPagination"}

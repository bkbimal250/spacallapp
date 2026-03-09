from .base import *

DEBUG = False

# Pull allowed hosts from .env (comma-separated list)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=['api.spa.branch.call.workspa.in', 'localhost', '127.0.0.1'])

# Temporarily allowing all origins to debug the "Network Error" on login
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    'https://spacallapp.dishaonlinesolution.in',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
])

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    'https://api.spa.branch.call.workspa.in',
    'https://spacallapp.dishaonlinesolution.in',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
])

# Use WhiteNoise for static files in production
# Insert it after SecurityMiddleware
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(index + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Use SSL/HTTPS settings in production
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Necessary if the app is behind a proxy like Nginx that terminates SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django-error.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Ensure log directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

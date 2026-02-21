from .base import *

DEBUG = False

ALLOWED_HOSTS = ['api.spa.branch.call.workspa.in', 'localhost', '127.0.0.1']

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = [
    'https://api.spa.branch.call.workspa.in',
    'https://spacallapp.dishaonlinesolution.in' # Assuming frontend might be here
]

# Necessary if the app is behind a proxy like Nginx that terminates SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

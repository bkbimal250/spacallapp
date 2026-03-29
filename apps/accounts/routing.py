from django.urls import re_path
from .consumers import CRMConsumer

websocket_urlpatterns = [
    re_path(r"ws/crm/dashboard/$", CRMConsumer.as_view()),
]

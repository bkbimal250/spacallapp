from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceEventViewSet, DeviceStatusResultView, DeviceHeartbeatView

router = DefaultRouter()
router.register(r'device-events', DeviceEventViewSet, basename='device-event')

urlpatterns = [
    path('status/', DeviceStatusResultView.as_view(), name='device-status'),
    path('heartbeat/', DeviceHeartbeatView.as_view(), name='device-heartbeat'),
    path('', include(router.urls)),
]

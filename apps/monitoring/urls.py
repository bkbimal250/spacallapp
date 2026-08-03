from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceEventViewSet,
    DeviceHeartbeatView,
    DeviceStatusResultView,
    PlatformHealthView,
    PlatformMetricsSummaryView,
    RecentRequestMetricsView,
    SlowQueryListView,
)

router = DefaultRouter()
router.register(r'device-events', DeviceEventViewSet, basename='device-event')

urlpatterns = [
    path('health/', PlatformHealthView.as_view(), name='platform-health'),
    path('platform/summary/', PlatformMetricsSummaryView.as_view(), name='platform-metrics-summary'),
    path('platform/requests/', RecentRequestMetricsView.as_view(), name='platform-request-metrics'),
    path('platform/slow-queries/', SlowQueryListView.as_view(), name='platform-slow-queries'),
    path('status/', DeviceStatusResultView.as_view(), name='device-status'),
    path('heartbeat/', DeviceHeartbeatView.as_view(), name='device-heartbeat'),
    path('', include(router.urls)),
]

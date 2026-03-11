from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminSendNotificationView, NotificationViewSet, NotificationStatsView

router = DefaultRouter()
router.register(r'logs', NotificationViewSet, basename='notification-logs')

urlpatterns = [
    path('send-manual/', AdminSendNotificationView.as_view(), name='send-manual-notification'),
    path('stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('', include(router.urls)),
]

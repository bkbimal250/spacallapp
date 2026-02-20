from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallLogViewSet, DeviceSyncView

router = DefaultRouter()
router.register(r'', CallLogViewSet, basename='calllog')

urlpatterns = [
    path('sync/', DeviceSyncView.as_view(), name='device-sync'),
    path('', include(router.urls)),
]

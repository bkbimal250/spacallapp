from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallLogViewSet, DeviceSyncView, MissedCallFollowUpViewSet

router = DefaultRouter()
router.register(r'followup', MissedCallFollowUpViewSet, basename='missed-call-followup')
router.register(r'', CallLogViewSet, basename='calllog')

urlpatterns = [
    path('sync/', DeviceSyncView.as_view(), name='device-sync'),
    path('stats/', CallLogViewSet.as_view({'get': 'stats'}), name='calllog-stats'),
    path('bulk_delete/', CallLogViewSet.as_view({'post': 'bulk_delete'}), name='calllog-bulk-delete'),
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeadManagementViewSet, LeadsSyncView

router = DefaultRouter()
router.register(r'sync', LeadsSyncView, basename='lead-sync')
router.register(r'', LeadManagementViewSet, basename='leadmanagement')

urlpatterns = [
    path('', include(router.urls)),
]

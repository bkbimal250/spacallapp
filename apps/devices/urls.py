from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, ClaimRegistrationView

router = DefaultRouter()
router.register(r'', DeviceViewSet, basename='device')

urlpatterns = [
    path('claim-registration/', ClaimRegistrationView.as_view(), name='claim-registration'),
    path('', include(router.urls)),
]


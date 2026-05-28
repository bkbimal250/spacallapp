from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, ClaimRegistrationView, RestoreRegistrationView, UpdateFCMTokenView

router = DefaultRouter()
router.register(r'', DeviceViewSet, basename='device')

urlpatterns = [
    path('claim-registration/', ClaimRegistrationView.as_view(), name='claim-registration'),
    path('restore-registration/', RestoreRegistrationView.as_view(), name='restore-registration'),
    path('update-fcm-token/', UpdateFCMTokenView.as_view(), name='update-fcm-token'),
    path('', include(router.urls)),
]


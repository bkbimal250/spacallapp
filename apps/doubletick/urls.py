from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DoubleTickLeadViewSet, DoubleTickMobileLeadViewSet, DoubleTickWebhookView


router = DefaultRouter()
router.register(r"leads", DoubleTickLeadViewSet, basename="doubletick-leads")
router.register(r"mobile/leads", DoubleTickMobileLeadViewSet, basename="doubletick-mobile-leads")

urlpatterns = [
    path("webhook/", DoubleTickWebhookView.as_view(), name="doubletick-webhook"),
    path("", include(router.urls)),
]

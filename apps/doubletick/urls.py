from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import DoubleTickLeadViewSet, DoubleTickMobileLeadViewSet, DoubleTickWebhookView


router = DefaultRouter()
router.register(r"leads", DoubleTickLeadViewSet, basename="doubletick-leads")
router.register(r"mobile/leads", DoubleTickMobileLeadViewSet, basename="doubletick-mobile-leads")

urlpatterns = [
    # Accept both /webhook and /webhook/ so DoubleTick POST callbacks are not
    # redirected by CommonMiddleware and accidentally retried as GET requests.
    re_path(r"^webhook/?$", DoubleTickWebhookView.as_view(), name="doubletick-webhook"),
    path("", include(router.urls)),
]

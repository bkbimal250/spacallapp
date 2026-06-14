from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    DoubleTickConversationViewSet,
    DoubleTickDashboardMetricsView,
    DoubleTickLeadViewSet,
    DoubleTickMobileLeadViewSet,
    DoubleTickWebhookView,
)


router = DefaultRouter()
router.register(r"conversations", DoubleTickConversationViewSet, basename="doubletick-conversations")
router.register(r"leads", DoubleTickLeadViewSet, basename="doubletick-leads")
router.register(r"mobile/leads", DoubleTickMobileLeadViewSet, basename="doubletick-mobile-leads")

urlpatterns = [
    # Accept both /webhook and /webhook/ so DoubleTick POST callbacks are not
    # redirected by CommonMiddleware and accidentally retried as GET requests.
    re_path(r"^webhook/?$", DoubleTickWebhookView.as_view(), name="doubletick-webhook"),
    path("metrics/", DoubleTickDashboardMetricsView.as_view(), name="doubletick-metrics"),
    path("", include(router.urls)),
]

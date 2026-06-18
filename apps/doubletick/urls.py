from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    DoubleTickAreaAliasViewSet,
    DoubleTickConversationViewSet,
    DoubleTickDashboardMetricsView,
    DoubleTickDistributionAuditViewSet,
    DoubleTickLeadAreaBranchViewSet,
    DoubleTickLeadAreaViewSet,
    DoubleTickLeadViewSet,
    DoubleTickMobileLeadViewSet,
    DoubleTickWebhookView,
)


router = DefaultRouter()
router.register(r"areas", DoubleTickLeadAreaViewSet, basename="doubletick-areas")
router.register(r"area-aliases", DoubleTickAreaAliasViewSet, basename="doubletick-area-aliases")
router.register(r"area-branches", DoubleTickLeadAreaBranchViewSet, basename="doubletick-area-branches")
router.register(r"distribution-audits", DoubleTickDistributionAuditViewSet, basename="doubletick-distribution-audits")
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

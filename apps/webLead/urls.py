from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicWebsiteFormConfigView,
    WebsiteFormConfigurationViewSet,
    WebsiteLeadAnalyticsOverviewView,
    WebsiteLeadAssignView,
    WebsiteLeadBranchAnalyticsView,
    WebsiteLeadFormAnalyticsView,
    WebsiteLeadSubmitView,
    WebsiteLeadViewSet,
    WebsiteLeadWebsiteAnalyticsView,
)

router = DefaultRouter()
router.register("configurations", WebsiteFormConfigurationViewSet, basename="web-lead-configurations")
router.register("leads", WebsiteLeadViewSet, basename="web-leads")

urlpatterns = [
    path("submit/", WebsiteLeadSubmitView.as_view(), name="web-lead-submit"),
    path("config/<str:form_key>/", PublicWebsiteFormConfigView.as_view(), name="web-lead-public-config"),
    path("leads/<uuid:pk>/assign/", WebsiteLeadAssignView.as_view(), name="web-lead-assign"),
    path("analytics/overview/", WebsiteLeadAnalyticsOverviewView.as_view(), name="web-lead-analytics-overview"),
    path("analytics/branches/", WebsiteLeadBranchAnalyticsView.as_view(), name="web-lead-analytics-branches"),
    path("analytics/websites/", WebsiteLeadWebsiteAnalyticsView.as_view(), name="web-lead-analytics-websites"),
    path("analytics/forms/", WebsiteLeadFormAnalyticsView.as_view(), name="web-lead-analytics-forms"),
    path("", include(router.urls)),
]

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.callrouting.views import RoutingRequestViewSet, RoutingRuleViewSet

router = DefaultRouter()
router.register("requests", RoutingRequestViewSet, basename="callrouting-request")
router.register("rules", RoutingRuleViewSet, basename="callrouting-rule")

urlpatterns = [
    path("", include(router.urls)),
]

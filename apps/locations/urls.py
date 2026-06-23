# apps/locations/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AreaAliasViewSet,
    AreaViewSet,
    BranchCoverageAreaViewSet,
    CityAliasViewSet,
    CityViewSet,
    LocationAnalyticsAPIView,
    LocationGroupAreaViewSet,
    LocationGroupViewSet,
    LocationMatchAPIView,
    LocationMatchIgnorePhraseViewSet,
    StateViewSet,
)

app_name = "locations"

router = DefaultRouter()

router.register(
    r"states",
    StateViewSet,
    basename="location-states",
)

router.register(
    r"cities",
    CityViewSet,
    basename="location-cities",
)

router.register(
    r"city-aliases",
    CityAliasViewSet,
    basename="location-city-aliases",
)

router.register(
    r"areas",
    AreaViewSet,
    basename="location-areas",
)

router.register(
    r"area-aliases",
    AreaAliasViewSet,
    basename="location-area-aliases",
)

router.register(
    r"groups",
    LocationGroupViewSet,
    basename="location-groups",
)

router.register(
    r"group-areas",
    LocationGroupAreaViewSet,
    basename="location-group-areas",
)

router.register(
    r"branch-coverages",
    BranchCoverageAreaViewSet,
    basename="location-branch-coverages",
)

router.register(
    r"ignore-phrases",
    LocationMatchIgnorePhraseViewSet,
    basename="location-ignore-phrases",
)

urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "match/",
        LocationMatchAPIView.as_view(),
        name="location-match",
    ),
    path(
        "analytics/",
        LocationAnalyticsAPIView.as_view(),
        name="location-analytics",
    ),
]
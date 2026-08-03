from django.urls import path

from .views_v2 import (
    DashboardV2BranchesView,
    DashboardV2ContactsView,
    DashboardV2DevicesView,
    DashboardV2ExportsView,
    DashboardV2SummaryView,
    DashboardV2TrendsView,
    DashboardV2UsersView,
)

urlpatterns = [
    path("summary/", DashboardV2SummaryView.as_view(), name="dashboard-v2-summary"),
    path("devices/", DashboardV2DevicesView.as_view(), name="dashboard-v2-devices"),
    path("branches/", DashboardV2BranchesView.as_view(), name="dashboard-v2-branches"),
    path("trends/", DashboardV2TrendsView.as_view(), name="dashboard-v2-trends"),
    path("users/", DashboardV2UsersView.as_view(), name="dashboard-v2-users"),
    path("contacts/", DashboardV2ContactsView.as_view(), name="dashboard-v2-contacts"),
    path("exports/", DashboardV2ExportsView.as_view(), name="dashboard-v2-exports"),
]

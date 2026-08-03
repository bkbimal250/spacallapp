from django.urls import path

from .views import (
    DashboardBranchesView,
    DashboardContactsView,
    DashboardDevicesView,
    DashboardExportsView,
    DashboardOverviewView,
    DashboardStatsView,
    DashboardSummaryView,
    DashboardTrendsView,
    DashboardUsersView,
)

urlpatterns = [
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('devices/', DashboardDevicesView.as_view(), name='dashboard-devices'),
    path('branches/', DashboardBranchesView.as_view(), name='dashboard-branches'),
    path('trends/', DashboardTrendsView.as_view(), name='dashboard-trends'),
    path('users/', DashboardUsersView.as_view(), name='dashboard-users'),
    path('contacts/', DashboardContactsView.as_view(), name='dashboard-contacts'),
    path('exports/', DashboardExportsView.as_view(), name='dashboard-exports'),
]

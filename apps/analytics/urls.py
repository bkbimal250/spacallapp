from django.urls import path
from .views import (
    AnalyticsOverviewView, PeakHoursView, AnalyticsStatsView,
    CallAnalyticsView, LeadAnalyticsView
)

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('peak-hours/', PeakHoursView.as_view(), name='analytics-peak-hours'),
    path('stats/', AnalyticsStatsView.as_view(), name='analytics-stats'),
    path('calls/', CallAnalyticsView.as_view(), name='analytics-calls'),
    path('leads/', LeadAnalyticsView.as_view(), name='analytics-leads'),
]

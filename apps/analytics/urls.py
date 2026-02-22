from django.urls import path
from .views import AnalyticsOverviewView, PeakHoursView, AnalyticsStatsView

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('peak-hours/', PeakHoursView.as_view(), name='analytics-peak-hours'),
    path('stats/', AnalyticsStatsView.as_view(), name='analytics-stats'),
]

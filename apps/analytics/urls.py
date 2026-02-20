from django.urls import path
from .views import AnalyticsOverviewView, PeakHoursView

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('peak-hours/', PeakHoursView.as_view(), name='analytics-peak-hours'),
]

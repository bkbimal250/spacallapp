from celery import shared_task
from django.contrib.auth import get_user_model

from apps.common.feature_flags import background_analytics_enabled, redis_cache_enabled

from .services import (
    DashboardAnalyticsService,
    DashboardBranchService,
    DashboardContactService,
    DashboardDeviceService,
    DashboardExportService,
    DashboardSummaryService,
    DashboardStatisticsService,
    DashboardTrendService,
    DashboardUserService,
)


@shared_task(ignore_result=True)
def warm_dashboard_cache():
    if not redis_cache_enabled():
        return

    User = get_user_model()
    users = User.objects.filter(is_active=True, role__in=["super_admin", "admin", "area_manager", "spa_manager"]).only(
        "id",
        "role",
        "branch",
    )
    default_params = {}

    for user in users.iterator(chunk_size=200):
        DashboardSummaryService.get(user, default_params, use_cache=True)
        DashboardDeviceService.get(user, default_params, use_cache=True)
        DashboardBranchService.get(user, default_params, use_cache=True)
        DashboardTrendService.get(user, default_params, use_cache=True)
        DashboardUserService.get(user, default_params, use_cache=True)
        DashboardContactService.get(user, default_params, use_cache=True)
        DashboardExportService.get(user, default_params, use_cache=True)
        DashboardAnalyticsService.legacy_stats(user, default_params, use_cache=True)


@shared_task(ignore_result=True)
def refresh_dashboard_statistics():
    if not background_analytics_enabled():
        return

    DashboardStatisticsService.refresh_for_date()

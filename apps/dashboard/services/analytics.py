from .branches import DashboardBranchService
from .summary import DashboardSummaryService
from .trends import DashboardTrendService


class DashboardAnalyticsService:
    @classmethod
    def legacy_stats(cls, user, params=None, request=None, use_cache=True):
        return {
            **DashboardSummaryService.get(user, params=params, request=request, use_cache=use_cache),
            "call_volume_trends": [
                {
                    "name": item["name"],
                    "calls": item["calls"],
                }
                for item in DashboardTrendService.get(user, params=params, request=request, use_cache=use_cache)
            ],
            "branch_performance": DashboardBranchService.get(
                user,
                params=params,
                request=request,
                use_cache=use_cache,
            ),
        }

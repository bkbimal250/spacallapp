from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from .views import (
    DashboardBranchesView,
    DashboardContactsView,
    DashboardDevicesView,
    DashboardExportsView,
    DashboardSummaryView,
    DashboardTrendsView,
    DashboardUsersView,
)


class DashboardV2FlagMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "ENABLE_DASHBOARD_V2", True):
            return Response(
                {"error": "Dashboard v2 is disabled."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return super().dispatch(request, *args, **kwargs)


class DashboardV2SummaryView(DashboardV2FlagMixin, DashboardSummaryView):
    pass


class DashboardV2DevicesView(DashboardV2FlagMixin, DashboardDevicesView):
    pass


class DashboardV2BranchesView(DashboardV2FlagMixin, DashboardBranchesView):
    pass


class DashboardV2TrendsView(DashboardV2FlagMixin, DashboardTrendsView):
    pass


class DashboardV2UsersView(DashboardV2FlagMixin, DashboardUsersView):
    pass


class DashboardV2ContactsView(DashboardV2FlagMixin, DashboardContactsView):
    pass


class DashboardV2ExportsView(DashboardV2FlagMixin, DashboardExportsView):
    pass

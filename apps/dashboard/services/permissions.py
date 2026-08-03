from apps.common.utils import get_branch_filter_ids


class DashboardPermissionService:
    @staticmethod
    def branch_scope_for_user(user):
        return get_branch_filter_ids(user)

    @staticmethod
    def can_see_no_data(user):
        return DashboardPermissionService.branch_scope_for_user(user) == ["NONE"]

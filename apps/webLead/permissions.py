from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin_user(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, "role", None) in ["super_admin", "admin"]
    )


def branch_ids_for_user(user):
    if not user or not user.is_authenticated:
        return []
    role = getattr(user, "role", None)
    if role in ["super_admin", "admin"]:
        return None
    if role == "spa_manager" and user.branch_id:
        return [user.branch_id]
    if role == "area_manager":
        return list(user.area_branches.values_list("id", flat=True))
    return []


class IsWebLeadConfigurationUser(BasePermission):
    message = "You do not have permission to manage website form configurations."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_admin_user(request.user)


class IsWebLeadUser(BasePermission):
    message = "You do not have permission to access this website lead."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrSuperAdmin(BasePermission):
    message = "Only admins and super admins can perform this action."

    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsSuperAdmin(BasePermission):
    message = "Only super admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "super_admin"
        )

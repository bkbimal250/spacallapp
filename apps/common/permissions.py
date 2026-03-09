"""
Custom DRF permissions for the CallLog SPA Management System.

Role hierarchy:
    super_admin  → Full access to everything.
    admin        → Manage branches, users, devices. View all data.
    branch_manager → Read/update only for their assigned branch.

Usage in views:
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    permission_classes = [IsAuthenticated]  # All 3 roles — filter in get_queryset()
"""

from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Allow access only to users with the 'super_admin' role.
    Used for destructive operations like permanently deleting data.
    """

    message = "Only Super Admins can perform this action."

    def has_permission(self, request, view):
        # Ensure user is authenticated and has the super_admin role
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == "super_admin"
        )


class IsAdminOrSuperAdmin(BasePermission):
    """
    Allow access to 'admin' and 'super_admin' roles.
    Used for user management, branch creation, and device management.
    """

    message = "Only Admins or Super Admins can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role in ["super_admin", "admin"]
        )


class IsBranchManager(BasePermission):
    """
    Allow access to 'branch_manager' role.
    Used to restrict certain views to branch managers only.
    """

    message = "Only Branch Managers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == "branch_manager"
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Allow write access only to admins and super admins.
    Read access is open to all authenticated users.
    """

    def has_permission(self, request, view):
        from rest_framework.permissions import SAFE_METHODS
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role in ["super_admin", "admin"]
        )

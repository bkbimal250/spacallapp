from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        # Assuming role field exists or checking existing is_superuser
        # User requested: return request.user.role == "super_admin"
        # We'll check if 'role' exists, else fall back to is_superuser
        if hasattr(request.user, 'role'):
            return request.user.role == "super_admin"
        return request.user.is_superuser

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        if hasattr(request.user, 'role'):
            return request.user.role in ["super_admin", "admin"]
        return request.user.is_superuser or request.user.is_staff

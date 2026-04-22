from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.created_by == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsDevice(permissions.BasePermission):
    """
    Allows access only to authenticated devices.
    """
    def has_permission(self, request, view):
        return bool(request.auth and hasattr(request.auth, 'device_id'))

class IsAdmin(permissions.BasePermission):
    """
    Allows access only to users with 'admin' or 'super_admin' roles.
    """
    def has_permission(self, request, view):
        return bool(request.user and hasattr(request.user, 'role') and request.user.role in ['admin', 'super_admin'])

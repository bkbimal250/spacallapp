"""
Views for the Branches app.

Endpoints:
    GET /branches/          → List branches (filtered by role).
    POST /branches/         → Create branch (admin/super_admin only).
    PUT/PATCH /branches/<id>/ → Update branch (admin/super_admin only).
    DELETE /branches/<id>/  → Delete branch (super_admin only).

Access Control:
    super_admin   → Full CRUD on all branches.
    admin         → Full CRUD on all branches.
    branch_manager → Read-only, see only their assigned branch.

Filters:
    ?search=<name_or_code>  → Search by spa_name or branch code.
    ?city=<city>            → Filter by city.
    ?status=true|false      → Filter by is_active status.
"""

from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .models import Branch
from .serializers import BranchSerializer
from apps.common.permissions import IsAdminOrSuperAdmin


class BranchViewSet(viewsets.ModelViewSet):
    """
    CRUD for Branch (Spa locations).

    Access:
        All authenticated users can list/read branches.
        Only admin and super_admin can create/update/delete.
        Branch managers only see their own assigned branch.
    """
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Apply stricter permissions for write operations.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Return branches based on the user's role:
            super_admin / admin → All branches.
            branch_manager      → Only their assigned branch.
        Apply optional search/filter query params.
        """
        user = self.request.user
        queryset = Branch.objects.all().order_by("spa_name")

        # Branch managers can only see their own assigned branch
        if user.role == "branch_manager":
            if user.branch:
                queryset = queryset.filter(id=user.branch.id)
            else:
                # No branch assigned — return empty queryset
                queryset = queryset.none()

        # Admin and super_admin see all branches — no filter needed

        # ─── Optional Filters ─────────────────────────────────────────────────

        # Search by spa name or branch code
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                models.Q(spa_name__icontains=search) |
                models.Q(code__icontains=search)
            )

        # Filter by city
        city = self.request.query_params.get("city", None)
        if city:
            queryset = queryset.filter(city__icontains=city)

        # Filter by active status (accepts 'true' or 'false' string)
        is_active = self.request.query_params.get("status", None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        return queryset

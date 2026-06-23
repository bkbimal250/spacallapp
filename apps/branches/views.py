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
    ?search=<branch_city_area_code>  → Search by branch name, city, area, spa code, phone, address, or group.
    ?city=<city>            → Filter by city.
    ?state=<state>          → Filter by state.
    ?status=true|false      → Filter by is_active status.
"""

from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import Branch, BranchGroups
from .serializers import BranchSerializer, BranchListSerializer, BranchGroupSerializer
from .filters import BranchFilter, BranchGroupFilter
from core.pagination import StandardResultsSetPagination
from apps.common.permissions import IsAdminOrSuperAdmin
from apps.common.utils import apply_branch_filter


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
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = BranchFilter

    def get_serializer_class(self):
        """
        Use a lean serializer for the list action to improve performance.
        """
        if self.action == "list":
            return BranchListSerializer
        return BranchSerializer

    def get_permissions(self):
        """
        Apply stricter permissions for write operations.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        summary="List Branches",
        parameters=[
            OpenApiParameter("all", type=bool, description="Set to true to disable pagination"),
            OpenApiParameter("search", type=str, description="Search by branch name, city, area, spa code, phone, address, or group"),
            OpenApiParameter("city", type=str, description="Filter by city"),
            OpenApiParameter("state", type=str, description="Filter by state"),
            OpenApiParameter("status", type=bool, description="Filter by active status"),
            OpenApiParameter("group", type=str, description="Filter by branch group UUID"),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        List branches with role-based caching.
        """
        # Disable pagination if ?all=true
        if request.query_params.get("all", "false").lower() == "true":
            self.pagination_class = None

        # Determine cache key based on user role and query params
        user = request.user
        role = getattr(user, 'role', 'anonymous')
        branch_id = getattr(user.branch, 'id', 'none') if hasattr(user, 'branch') and user.branch else 'none'
        if role == "area_manager":
            branch_id = "_".join(str(b) for b in user.area_branches.values_list("id", flat=True)) or "none"

        cache_key = f"branches_list_{role}_{branch_id}_{request.get_full_path()}"

        # Try to get from cache
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)

        # Cache for 15 minutes if successful
        if response.status_code == 200:
            cache.set(cache_key, response.data, 60 * 15)

        return response

    def perform_create(self, serializer):
        serializer.save()
        self._clear_cache()

    def perform_update(self, serializer):
        serializer.save()
        self._clear_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self._clear_cache()

    def _clear_cache(self):
        """Clear branch related cache."""
        cache.delete_pattern("branches_list_*")

    def get_queryset(self):
        """
        Return branches based on the user's role:
            super_admin / admin → All branches.
            branch_manager      → Only their assigned branch.
        Apply optional search/filter query params.
        """
        if getattr(self, "swagger_fake_view", False):
            return Branch.objects.none()

        user = self.request.user
        queryset = Branch.objects.select_related(
            "branch_group",
            "location_state",
            "location_city",
            "location_group",
            "location_area",
        ).all().order_by("spa_name")

        # Optimization: prune columns for the list view
        if self.action == "list":
            # Select related to avoid N+1; include all fields for BranchListSerializer
            queryset = queryset.only(
                "id", "spa_name", "code", "city", "area", "state", "postal_code", "address", "phone", "is_active",
                "branch_group_id", "branch_group__name",
                "location_state_id", "location_state__name",
                "location_city_id", "location_city__name",
                "location_group_id", "location_group__name",
                "location_area_id", "location_area__name",
            )

        # Branch managers / spa_managers can only see their own assigned branch
        if user.is_authenticated and hasattr(user, 'role') and user.role in ["spa_manager", "area_manager"]:
            if user.role == "area_manager":
                queryset = apply_branch_filter(queryset, "id", user)
            elif user.branch:
                queryset = queryset.filter(id=user.branch.id)
            else:
                queryset = queryset.none()
            return queryset

        # Admin and super_admin see all branches — no filter needed
        return queryset


class BranchGroupViewSet(viewsets.ModelViewSet):
    """
    CRUD for Branch Groups.
    """
    serializer_class = BranchGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BranchGroupFilter

    def get_queryset(self):
        """
        Return branch groups with optional filtering.
        """
        if getattr(self, "swagger_fake_view", False):
            return BranchGroups.objects.none()

        queryset = BranchGroups.objects.annotate(branch_count=Count("branches")).all().order_by("name")
        return queryset

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "assign_branches"]:
            return [permissions.IsAuthenticated(), IsAdminOrSuperAdmin()]
        return [permissions.IsAuthenticated()]

    @extend_schema(summary="List Branch Groups")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create Branch Group")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Branch Group")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update Branch Group")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial Update Branch Group")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete Branch Group")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Assign Branches to Group",
        description="Bulk assign a list of branch IDs to this group (replacing current members).",
        request=inline_serializer(
            name="AssignBranchesRequest",
            fields={
                "branch_ids": serializers.ListField(child=serializers.UUIDField())
            }
        ),
        responses={200: inline_serializer(
            name="AssignBranchesResponse",
            fields={"status": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post'])
    def assign_branches(self, request, pk=None):
        group = self.get_object()
        branch_ids = request.data.get('branch_ids', [])

        try:
            with transaction.atomic():
                # Unassign branches currently in this group
                Branch.objects.filter(branch_group=group).update(branch_group=None)
                # Assign selected branches to this group
                if branch_ids:
                    Branch.objects.filter(id__in=branch_ids).update(branch_group=group)
            return Response({"status": "Branches assigned successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

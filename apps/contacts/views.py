"""
Contact views for the CallLog SPA Management System.

Contacts are phone numbers linked to known customers.
When a call log comes in, the phone number is matched to a contact.

Access Control:
    super_admin / admin → See and manage all contacts.
    spa_manager         → See only contacts whose call logs belong to their branch,
                          or contacts they created themselves.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count

from .models import Contact
from .serializers import ContactSerializer
from .services import ContactService
from apps.common.permissions import IsSuperAdmin
from apps.common.utils import get_branch_filter_ids
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ContactFilter


class ContactViewSet(viewsets.ModelViewSet):
    """
    Contact CRUD viewset.

    Contacts are global records (phone_number is unique across the system).
    SPA managers can see contacts relevant to their branch calls
    but cannot see contacts that belong to other branches.

    Filters:
        ?search=<name_or_phone>    → Search by name or phone number.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContactFilter

    def get_permissions(self):
        """Delete contacts is restricted to super_admin only."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsSuperAdmin()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List Contacts",
        parameters=[]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create Contact")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Contact")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update Contact")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial Update Contact")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete Contact (SuperAdmin Only)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return contacts filtered by the user's role and branch access.
        """
        user = self.request.user

        # Handle schema generation and unauthenticated access
        if not user or not user.is_authenticated or getattr(self, "swagger_fake_view", False):
            if getattr(self, "swagger_fake_view", False):
                return Contact.objects.annotate(total_calls=Count("call_logs")).all()
            return Contact.objects.none()

        queryset = Contact.objects.annotate(
            total_calls=Count("call_logs")
        ).all().order_by("-created_at")

        # Optimization: prune columns for the list view
        if self.action == "list":
            queryset = queryset.only(
                "id", "name", "phone_number", "email", "country", "city", "created_at"
            )

        # Admin and super_admin see all contacts globally
        if user.role in ["super_admin", "admin"]:
            pass  # No additional filter needed

        elif user.role in ["spa_manager", "area_manager"]:
            branch_ids = get_branch_filter_ids(user)
            if user.role == "area_manager" and branch_ids != ["NONE"]:
                queryset = queryset.filter(
                    Q(call_logs__branch_id__in=branch_ids) |
                    Q(created_by=user) |
                    Q(created_by__branch_id__in=branch_ids)
                ).distinct()
            elif user.role == "spa_manager" and user.branch:
                # Show contacts that have call activity in this branch,
                # OR were manually created by someone in this branch
                queryset = queryset.filter(
                    Q(call_logs__branch=user.branch) |
                    Q(created_by=user) |
                    Q(created_by__branch=user.branch)
                ).distinct()
            else:
                # SPA manager with no assigned branch — return nothing
                return queryset.none()

        # Search filter is now handled by DjangoFilterBackend via ContactFilter
        
        return queryset

    def perform_create(self, serializer):
        """Create contact and link to call logs automatically via Contact.save()."""
        ContactService.create_contact(serializer.validated_data, self.request.user)

    def perform_update(self, serializer):
        """Update contact details."""
        ContactService.update_contact(self.get_object(), serializer.validated_data, self.request.user)

    def perform_destroy(self, instance):
        """Delete contact (super_admin only)."""
        ContactService.delete_contact(instance)

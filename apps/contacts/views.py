"""
Contact views for the CallLog SPA Management System.

Contacts are phone numbers linked to known customers.
When a call log comes in, the phone number is matched to a contact.

Access Control:
    super_admin / admin → See and manage all contacts.
    branch_manager      → See only contacts whose call logs belong to their branch,
                          or contacts they created themselves.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Contact
from .serializers import ContactSerializer
from .services import ContactService
from apps.common.permissions import IsSuperAdmin


class ContactViewSet(viewsets.ModelViewSet):
    """
    Contact CRUD viewset.

    Contacts are global records (phone_number is unique across the system).
    Branch managers can see contacts relevant to their branch calls
    but cannot see contacts that belong to other branches.

    Filters:
        ?search=<name_or_phone>    → Search by name or phone number.
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Delete contacts is restricted to super_admin only."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsSuperAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Return contacts filtered by the user's role and branch access.

        super_admin / admin → All contacts.
        branch_manager      → Contacts that have call logs in their branch,
                              OR contacts they created themselves.
        """
        user = self.request.user
        queryset = Contact.objects.all().order_by("-created_at")

        # Admin and super_admin see all contacts globally
        if user.role in ["super_admin", "admin"]:
            pass  # No additional filter needed

        elif user.role == "branch_manager":
            if user.branch:
                # Show contacts that have call activity in this branch,
                # OR were manually created by someone in this branch
                queryset = queryset.filter(
                    Q(call_logs__branch=user.branch) |
                    Q(created_by=user) |
                    Q(created_by__branch=user.branch)
                ).distinct()
            else:
                # Branch manager with no assigned branch — return nothing
                return queryset.none()

        # Search filter
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone_number__icontains=search)
            )

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

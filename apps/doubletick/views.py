from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.utils import apply_branch_filter
from apps.devices.models import Device
from core.authentication import DeviceAuthentication

from .filters import DoubleTickLeadFilter
from .models import DoubleTickLead, DoubleTickLeadActivity
from .serializers import (
    DoubleTickLeadActivitySerializer,
    DoubleTickLeadAssignSerializer,
    DoubleTickLeadDetailSerializer,
    DoubleTickLeadListSerializer,
    DoubleTickLeadSerializer,
    DoubleTickLeadStatusUpdateSerializer,
    DoubleTickWebhookSerializer,
)
from .services import create_or_update_lead_from_webhook, send_lead_notification
from .webhook import is_valid_doubletick_webhook


class IsAuthenticatedUserOrDevice(permissions.BasePermission):
    """Allow either a logged-in CRM user or an authenticated Android device."""

    def has_permission(self, request, view):
        user_ok = bool(request.user and getattr(request.user, "is_authenticated", False))
        device_ok = bool(request.auth and hasattr(request.auth, "device_id"))
        return user_ok or device_ok


def _role_filtered_leads(queryset, user):
    """
    Apply the CRM role model to DoubleTick leads.

    Admin roles see all WhatsApp leads. Area and spa managers are restricted to
    the branch relationships that already exist on the User model.
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    if getattr(user, "role", None) in ["super_admin", "admin"]:
        return queryset
    if getattr(user, "role", None) == "area_manager":
        return apply_branch_filter(queryset, "assigned_branch_id", user)
    if getattr(user, "role", None) == "spa_manager":
        if not user.branch_id:
            return queryset.filter(assigned_user=user)
        return queryset.filter(Q(assigned_branch=user.branch) | Q(assigned_user=user)).distinct()
    return queryset.none()


def _set_status_timestamp(lead, new_status):
    now = timezone.now()
    if new_status == DoubleTickLead.Status.OPENED and not lead.opened_at:
        lead.opened_at = now
    elif new_status == DoubleTickLead.Status.CONTACTED and not lead.contacted_at:
        lead.contacted_at = now
    elif new_status == DoubleTickLead.Status.FOLLOW_UP:
        lead.follow_up_at = now
    elif new_status == DoubleTickLead.Status.BOOKED and not lead.booked_at:
        lead.booked_at = now


class DoubleTickLeadViewSet(viewsets.ModelViewSet):
    """
    Web CRM API for DoubleTick leads.

    This viewset is deliberately separate from apps.leadmanagement so dashboard
    users can manage WhatsApp leads without changing call-log lead behavior.
    """

    serializer_class = DoubleTickLeadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DoubleTickLeadFilter
    search_fields = ["customer_name", "whatsapp_name", "phone_number", "city", "area", "doubletick_chat_id"]
    ordering_fields = ["created_at", "assigned_at", "status", "city", "area"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DoubleTickLead.objects.none()
        queryset = DoubleTickLead.objects.select_related(
            "assigned_branch",
            "assigned_user",
            "assigned_device",
            "duplicate_of",
        ).prefetch_related("activities")
        return _role_filtered_leads(queryset, self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return DoubleTickLeadListSerializer
        if self.action == "retrieve":
            return DoubleTickLeadDetailSerializer
        return DoubleTickLeadSerializer

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """
        Manually assign or reassign a lead from the dashboard.

        Admins can select branch/user/device explicitly. Restricted roles can
        only assign within the scoped queryset returned by get_object().
        """
        lead = self.get_object()
        serializer = DoubleTickLeadAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        User = get_user_model()
        branch_id = data.get("assigned_branch")
        user_id = data.get("assigned_user")
        device_id = data.get("assigned_device")

        if branch_id is not None:
            lead.assigned_branch_id = branch_id
        if user_id is not None:
            lead.assigned_user = User.objects.filter(id=user_id).first()
        if device_id is not None:
            lead.assigned_device = Device.objects.filter(id=device_id).first()

        lead.status = DoubleTickLead.Status.ASSIGNED if (lead.assigned_user or lead.assigned_device) else DoubleTickLead.Status.UNASSIGNED
        lead.assigned_at = timezone.now() if lead.status == DoubleTickLead.Status.ASSIGNED else None
        lead.save()

        DoubleTickLeadActivity.objects.create(
            lead=lead,
            user=request.user,
            action=DoubleTickLeadActivity.Action.REASSIGNED,
            note=data.get("note", ""),
            metadata={
                "assigned_branch": str(lead.assigned_branch_id) if lead.assigned_branch_id else None,
                "assigned_user": str(lead.assigned_user_id) if lead.assigned_user_id else None,
                "assigned_device": str(lead.assigned_device_id) if lead.assigned_device_id else None,
            },
        )
        send_lead_notification(lead)
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def activity(self, request, pk=None):
        """Add a note activity to a DoubleTick lead."""
        lead = self.get_object()
        serializer = DoubleTickLeadActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = DoubleTickLeadActivity.objects.create(
            lead=lead,
            user=request.user,
            action=serializer.validated_data.get("action", DoubleTickLeadActivity.Action.NOTE),
            note=serializer.validated_data.get("note", ""),
            metadata=serializer.validated_data.get("metadata", {}),
        )
        return Response(DoubleTickLeadActivitySerializer(activity).data, status=status.HTTP_201_CREATED)


class DoubleTickMobileLeadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lightweight mobile API.

    It supports either manager JWT auth or existing device header auth. A device
    sees only leads assigned to that device; a user sees only role-scoped leads
    assigned to them or their branch.
    """

    authentication_classes = [JWTAuthentication, DeviceAuthentication]
    permission_classes = [IsAuthenticatedUserOrDevice]
    serializer_class = DoubleTickLeadListSerializer

    def get_queryset(self):
        queryset = DoubleTickLead.objects.select_related("assigned_branch", "assigned_user", "assigned_device")
        device = getattr(self.request, "auth", None)
        if device and hasattr(device, "device_id"):
            return queryset.filter(assigned_device=device)

        user = self.request.user
        queryset = _role_filtered_leads(queryset, user)
        if getattr(user, "role", None) == "spa_manager":
            return queryset.filter(Q_assigned_to_user_or_branch(user))
        return queryset.filter(assigned_user=user) if getattr(user, "role", None) == "area_manager" else queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DoubleTickLeadDetailSerializer
        return DoubleTickLeadListSerializer

    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        lead = self.get_object()
        serializer = DoubleTickLeadStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        lead.status = new_status
        if new_status == DoubleTickLead.Status.LOST:
            lead.lost_reason = serializer.validated_data.get("lost_reason", lead.lost_reason)
        _set_status_timestamp(lead, new_status)
        lead.save()

        DoubleTickLeadActivity.objects.create(
            lead=lead,
            user=request.user if request.user and request.user.is_authenticated else None,
            device=self.request.auth if hasattr(self.request.auth, "device_id") else None,
            action=new_status,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        lead = self.get_object()
        if lead.status in [DoubleTickLead.Status.NEW, DoubleTickLead.Status.ASSIGNED]:
            lead.status = DoubleTickLead.Status.OPENED
        if not lead.opened_at:
            lead.opened_at = timezone.now()
        lead.save()

        DoubleTickLeadActivity.objects.create(
            lead=lead,
            user=request.user if request.user and request.user.is_authenticated else None,
            device=self.request.auth if hasattr(self.request.auth, "device_id") else None,
            action=DoubleTickLeadActivity.Action.OPENED,
            note="Lead opened from mobile.",
        )
        return Response(DoubleTickLeadDetailSerializer(lead).data)


def Q_assigned_to_user_or_branch(user):
    query = Q(assigned_user=user)
    if user.branch_id:
        query |= Q(assigned_branch_id=user.branch_id)
    return query


class DoubleTickWebhookView(APIView):
    """
    Public DoubleTick webhook endpoint protected by a shared secret.

    It intentionally does not use JWT because DoubleTick calls this endpoint
    server-to-server.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not is_valid_doubletick_webhook(request):
            return Response({"detail": "Invalid DoubleTick webhook secret."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DoubleTickWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead, webhook_log = create_or_update_lead_from_webhook(serializer.validated_data)
        return Response(
            {
                "status": "processed",
                "lead_id": str(lead.id),
                "webhook_log_id": str(webhook_log.id),
                "is_duplicate": lead.is_duplicate,
            },
            status=status.HTTP_201_CREATED,
        )

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.utils import apply_branch_filter
from apps.devices.models import Device
from core.authentication import DeviceAuthentication

from .filters import DoubleTickConversationFilter, DoubleTickLeadFilter
from .models import (
    DoubleTickActivity,
    DoubleTickAreaAlias,
    DoubleTickConversation,
    DoubleTickLead,
    DoubleTickLeadActivity,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadAssignment,
    DoubleTickLeadVisibility,
)
from .serializers import (
    DoubleTickActivitySerializer,
    DoubleTickAreaAliasSerializer,
    DoubleTickConversationAssignSupportSerializer,
    DoubleTickConversationDetailSerializer,
    DoubleTickConversationListSerializer,
    DoubleTickConversationMatchAreaSerializer,
    DoubleTickConversationReplySerializer,
    DoubleTickLeadActivitySerializer,
    DoubleTickLeadAreaBranchSerializer,
    DoubleTickLeadAreaSerializer,
    DoubleTickLeadAssignSerializer,
    DoubleTickLeadAssignmentSerializer,
    DoubleTickLeadDetailSerializer,
    DoubleTickLeadListSerializer,
    DoubleTickLeadSerializer,
    DoubleTickLeadStatusUpdateSerializer,
    DoubleTickMessageSerializer,
    DoubleTickWebhookSerializer,
)
from .services import (
    AreaMatchingService,
    DoubleTickChatService,
    DoubleTickReplyService,
    LeadClaimService,
    LeadDistributionService,
    LeadQualificationService,
    PendingConversationService,
    create_or_update_lead_from_webhook,
    normalize_area_text,
    send_lead_notification,
)
from .webhook import is_valid_doubletick_webhook


class IsAuthenticatedUserOrDevice(permissions.BasePermission):
    """Allow either a logged-in CRM user or an authenticated Android device."""

    def has_permission(self, request, view):
        user_ok = bool(request.user and getattr(request.user, "is_authenticated", False))
        device_ok = bool(request.auth and hasattr(request.auth, "device_id"))
        return user_ok or device_ok


class IsInternalCRMTeam(permissions.BasePermission):
    """Initially only admin/super_admin can operate the central team inbox."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in ["super_admin", "admin"]
        )


class DoubleTickAllListMixin:
    def list(self, request, *args, **kwargs):
        if request.query_params.get("all", "false").lower() == "true":
            self.pagination_class = None
        return super().list(request, *args, **kwargs)


class DoubleTickLeadAreaViewSet(DoubleTickAllListMixin, viewsets.ModelViewSet):
    """Admin CRUD for controlled CRM areas used by DoubleTick lead routing."""

    serializer_class = DoubleTickLeadAreaSerializer
    permission_classes = [IsInternalCRMTeam]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "city", "state", "distribution_mode"]
    search_fields = ["name", "city", "state", "normalized_name", "description"]
    ordering_fields = ["name", "city", "state", "priority", "created_at"]
    ordering = ["city", "priority", "name"]

    def get_queryset(self):
        return DoubleTickLeadArea.objects.annotate(
            alias_count=Count("aliases", distinct=True),
            branch_mapping_count=Count("branch_mappings", distinct=True),
        ).prefetch_related("aliases", "branch_mappings")


class DoubleTickAreaAliasViewSet(DoubleTickAllListMixin, viewsets.ModelViewSet):
    """Admin CRUD for customer location aliases mapped to controlled lead areas."""

    serializer_class = DoubleTickAreaAliasSerializer
    permission_classes = [IsInternalCRMTeam]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["lead_area", "channel", "is_active", "created_from_manual_mapping"]
    search_fields = ["alias", "normalized_alias", "lead_area__name", "lead_area__city"]
    ordering_fields = ["alias", "created_at"]
    ordering = ["alias"]

    def get_queryset(self):
        return DoubleTickAreaAlias.objects.select_related("lead_area", "channel")


class DoubleTickLeadAreaBranchViewSet(DoubleTickAllListMixin, viewsets.ModelViewSet):
    """Admin CRUD for mapping DoubleTick lead areas to receiving CRM branches."""

    serializer_class = DoubleTickLeadAreaBranchSerializer
    permission_classes = [IsInternalCRMTeam]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["lead_area", "branch", "is_active", "receives_leads"]
    search_fields = ["lead_area__name", "lead_area__city", "branch__spa_name", "branch__city", "branch__code"]
    ordering_fields = ["priority", "created_at", "branch__spa_name"]
    ordering = ["priority", "branch__spa_name"]

    def get_queryset(self):
        return DoubleTickLeadAreaBranch.objects.select_related("lead_area", "branch")


def _role_filtered_leads(queryset, user):
    if not user or not user.is_authenticated:
        return queryset.none()
    if getattr(user, "role", None) in ["super_admin", "admin"]:
        return queryset
    if getattr(user, "role", None) == "area_manager":
        branch_ids = user.area_branches.values_list("id", flat=True)
        return queryset.filter(Q(visibilities__branch_id__in=branch_ids) | Q(current_branch_id__in=branch_ids)).distinct()
    if getattr(user, "role", None) == "spa_manager":
        if not user.branch_id:
            return queryset.filter(current_user=user)
        return queryset.filter(Q(visibilities__branch=user.branch) | Q(current_user=user)).distinct()
    return queryset.none()


def _device_from_request(request):
    auth = getattr(request, "auth", None)
    return auth if auth and hasattr(auth, "device_id") else None


class DoubleTickConversationViewSet(viewsets.ModelViewSet):
    """Internal CRM team inbox for pending and qualified WhatsApp conversations."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DoubleTickConversationFilter
    search_fields = [
        "customer__customer_name",
        "customer__phone_number",
        "customer__dt_customer_id",
        "messages__text",
        "raw_city",
        "raw_area",
        "raw_service",
        "matched_area__name",
    ]
    ordering_fields = ["last_message_at", "first_message_at", "unread_count", "priority", "created_at"]
    ordering = ["-last_message_at", "-created_at"]

    def get_queryset(self):
        queryset = DoubleTickConversation.objects.select_related(
            "customer",
            "channel",
            "matched_area",
            "assigned_support_user",
            "current_lead",
        ).prefetch_related("messages")
        if getattr(self.request.user, "role", None) in ["super_admin", "admin"]:
            return queryset
        if getattr(self.request.user, "role", None) == "area_manager":
            branch_ids = self.request.user.area_branches.values_list("id", flat=True)
            return queryset.filter(current_lead__visibilities__branch_id__in=branch_ids).distinct()
        if getattr(self.request.user, "role", None) == "spa_manager":
            if not self.request.user.branch_id:
                return queryset.none()
            return queryset.filter(current_lead__visibilities__branch=self.request.user.branch).distinct()
        return queryset.none()

    def get_serializer_class(self):
        if self.action == "list":
            return DoubleTickConversationListSerializer
        return DoubleTickConversationDetailSerializer

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        queryset = DoubleTickChatService.get_chat(conversation)
        for field in ["direction", "origin", "status", "message_type"]:
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        sender = request.query_params.get("sender")
        if sender:
            queryset = queryset.filter(Q(sender_display_name__icontains=sender) | Q(sent_by__full_name__icontains=sender))
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(text__icontains=search) | Q(caption__icontains=search))
        if request.query_params.get("date_from"):
            queryset = queryset.filter(message_timestamp__date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            queryset = queryset.filter(message_timestamp__date__lte=request.query_params["date_to"])
        return Response(DoubleTickMessageSerializer(queryset, many=True).data)

    @action(detail=True, methods=["get"])
    def activities(self, request, pk=None):
        conversation = self.get_object()
        qs = conversation.timeline.select_related("user", "branch", "device")
        return Response(DoubleTickActivitySerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam], url_path="sync-chat")
    def sync_chat(self, request, pk=None):
        return Response(DoubleTickChatService.sync_chat(self.get_object()))

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def reply(self, request, pk=None):
        serializer = DoubleTickConversationReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = DoubleTickReplyService.reply(
                self.get_object(),
                request.user,
                serializer.validated_data["text"],
                serializer.validated_data.get("message_type", "text"),
            )
        except ValidationError as exc:
            detail = exc.detail[0] if isinstance(exc.detail, list) and exc.detail else exc.detail
            return Response({"detail": str(detail)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(DoubleTickMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam], url_path="request-location")
    def request_location(self, request, pk=None):
        try:
            message = DoubleTickReplyService.request_location(self.get_object(), request.user)
        except ValidationError as exc:
            detail = exc.detail[0] if isinstance(exc.detail, list) and exc.detail else exc.detail
            return Response({"detail": str(detail)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(DoubleTickMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam], url_path="match-area")
    def match_area(self, request, pk=None):
        conversation = self.get_object()
        serializer = DoubleTickConversationMatchAreaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead_area = DoubleTickLeadArea.objects.get(pk=serializer.validated_data["lead_area_id"])
        raw_alias = serializer.validated_data.get("raw_alias") or conversation.raw_area or lead_area.name
        conversation.matched_area = lead_area
        conversation.raw_area = raw_alias
        conversation.area_confirmed = True
        conversation.save(update_fields=["matched_area", "raw_area", "area_confirmed", "updated_at"])
        if serializer.validated_data.get("save_alias"):
            DoubleTickAreaAlias.objects.get_or_create(
                lead_area=lead_area,
                normalized_alias=normalize_area_text(raw_alias),
                defaults={"alias": raw_alias, "channel": conversation.channel, "created_from_manual_mapping": True},
            )
        if serializer.validated_data.get("qualify_as_lead"):
            lead = LeadQualificationService.qualify_conversation(conversation, user=request.user, distribute=True)
            return Response(DoubleTickLeadDetailSerializer(lead).data)
        AreaMatchingService.match_conversation(conversation, raw_area=raw_alias, save_alias=False)
        return Response(DoubleTickConversationDetailSerializer(conversation).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def qualify(self, request, pk=None):
        lead = LeadQualificationService.qualify_conversation(self.get_object(), user=request.user, distribute=True)
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam], url_path="assign-support")
    def assign_support(self, request, pk=None):
        conversation = self.get_object()
        serializer = DoubleTickConversationAssignSupportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        conversation.assigned_support_user = get_user_model().objects.filter(id=user_id).first() if user_id else None
        conversation.save(update_fields=["assigned_support_user", "updated_at"])
        return Response(DoubleTickConversationDetailSerializer(conversation).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam], url_path="mark-spam")
    def mark_spam(self, request, pk=None):
        conversation = self.get_object()
        old_status = conversation.status
        conversation.status = DoubleTickConversation.Status.SPAM
        conversation.save(update_fields=["status", "updated_at"])
        DoubleTickActivity.objects.create(conversation=conversation, user=request.user, action=DoubleTickActivity.Action.CLOSED, old_status=old_status, new_status=conversation.status, note="Marked spam.")
        return Response(DoubleTickConversationDetailSerializer(conversation).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def close(self, request, pk=None):
        conversation = self.get_object()
        old_status = conversation.status
        conversation.status = DoubleTickConversation.Status.CLOSED
        conversation.save(update_fields=["status", "updated_at"])
        DoubleTickActivity.objects.create(conversation=conversation, user=request.user, action=DoubleTickActivity.Action.CLOSED, old_status=old_status, new_status=conversation.status)
        return Response(DoubleTickConversationDetailSerializer(conversation).data)


class DoubleTickLeadViewSet(viewsets.ModelViewSet):
    """Web CRM API for qualified/distributed DoubleTick leads."""

    serializer_class = DoubleTickLeadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DoubleTickLeadFilter
    search_fields = ["customer_name", "phone_number", "raw_area", "matched_area__name", "doubletick_chat_id"]
    ordering_fields = ["created_at", "received_at", "claimed_at", "contacted_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = DoubleTickLead.objects.select_related(
            "conversation",
            "customer",
            "channel",
            "matched_area",
            "current_branch",
            "current_user",
            "current_device",
            "active_assignment",
            "assigned_branch",
            "assigned_user",
            "assigned_device",
        ).prefetch_related("visibilities", "assignments")
        return _role_filtered_leads(queryset, self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return DoubleTickLeadListSerializer
        if self.action == "retrieve":
            return DoubleTickLeadDetailSerializer
        return DoubleTickLeadSerializer

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        lead = self.get_object()
        return Response(DoubleTickMessageSerializer(lead.messages.all(), many=True).data)

    @action(detail=True, methods=["get"])
    def activities(self, request, pk=None):
        lead = self.get_object()
        return Response(DoubleTickActivitySerializer(lead.timeline.all(), many=True).data)

    @action(detail=True, methods=["get"])
    def assignments(self, request, pk=None):
        return Response(DoubleTickLeadAssignmentSerializer(self.get_object().assignments.all(), many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def distribute(self, request, pk=None):
        return Response(DoubleTickLeadDetailSerializer(LeadDistributionService.distribute(self.get_object(), user=request.user)).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def assign(self, request, pk=None):
        lead = self.get_object()
        serializer = DoubleTickLeadAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        User = get_user_model()
        if data.get("assigned_branch") is not None:
            lead.assigned_branch_id = data.get("assigned_branch")
            lead.current_branch_id = data.get("assigned_branch")
        if data.get("assigned_user") is not None:
            lead.assigned_user = User.objects.filter(id=data.get("assigned_user")).first()
            lead.current_user = lead.assigned_user
        if data.get("assigned_device") is not None:
            lead.assigned_device = Device.objects.filter(id=data.get("assigned_device")).first()
            lead.current_device = lead.assigned_device
        lead.status = DoubleTickLead.Status.CLAIMED if lead.current_user else DoubleTickLead.Status.AVAILABLE
        lead.assigned_at = timezone.now()
        lead.save()
        DoubleTickLeadActivity.objects.create(lead=lead, user=request.user, action=DoubleTickLeadActivity.Action.REASSIGNED, note=data.get("note", ""))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def reassign(self, request, pk=None):
        return self.assign(request, pk=pk)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        lead = LeadClaimService.release(pk, request.user, request.data.get("reason", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam])
    def close(self, request, pk=None):
        lead = self.get_object()
        lead.status = DoubleTickLead.Status.CLOSED
        lead.closed_reason = request.data.get("reason", "")
        lead.closed_at = timezone.now()
        lead.save(update_fields=["status", "closed_reason", "closed_at", "updated_at"])
        DoubleTickActivity.objects.create(lead=lead, user=request.user, action=DoubleTickActivity.Action.CLOSED, note=lead.closed_reason)
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def activity(self, request, pk=None):
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
    """Mobile-ready lead API supporting available/mine queues and claim/contact actions."""

    authentication_classes = [JWTAuthentication, DeviceAuthentication]
    permission_classes = [IsAuthenticatedUserOrDevice]
    serializer_class = DoubleTickLeadListSerializer

    def get_queryset(self):
        queryset = DoubleTickLead.objects.select_related("matched_area", "current_branch", "current_user", "active_assignment").prefetch_related("visibilities")
        device = _device_from_request(self.request)
        if device:
            return queryset.filter(visibilities__device=device, visibilities__is_visible=True).distinct()
        return _role_filtered_leads(queryset, self.request.user)

    def get_serializer_class(self):
        return DoubleTickLeadDetailSerializer if self.action == "retrieve" else DoubleTickLeadListSerializer

    @action(detail=False, methods=["get"])
    def available(self, request):
        queryset = self.get_queryset().filter(status=DoubleTickLead.Status.AVAILABLE)
        return Response(DoubleTickLeadListSerializer(queryset, many=True).data)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        queryset = self.get_queryset().filter(current_user=request.user)
        return Response(DoubleTickLeadListSerializer(queryset, many=True).data)

    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        assignment = LeadClaimService.claim(pk, request.user, _device_from_request(request))
        return Response(DoubleTickLeadAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "open", request.data.get("note", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], url_path="start-contact")
    def start_contact(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "start_contact", request.data.get("note", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        serializer = DoubleTickLeadStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_name = serializer.validated_data.get("action") or serializer.validated_data.get("status")
        lead = LeadClaimService.update_contact_status(pk, request.user, action_name, serializer.validated_data.get("note", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], url_path="follow-up")
    def follow_up(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "follow_up", request.data.get("note", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        lead = LeadClaimService.release(pk, request.user, request.data.get("reason", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)


class DoubleTickDashboardMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        conversations = DoubleTickConversation.objects.all()
        leads = DoubleTickLead.objects.all()
        return Response({
            "new_conversations_today": conversations.filter(created_at__date=today).count(),
            "greeting_only_conversations": conversations.filter(pending_reason=DoubleTickConversation.PendingReason.GREETING_ONLY).count(),
            "awaiting_location": conversations.filter(status=DoubleTickConversation.Status.AWAITING_LOCATION).count(),
            "awaiting_customer": conversations.filter(status=DoubleTickConversation.Status.AWAITING_CUSTOMER).count(),
            "manual_attention_required": conversations.filter(requires_manual_attention=True).count(),
            "unmatched_area": conversations.filter(status=DoubleTickConversation.Status.AREA_UNMATCHED).count(),
            "unread_conversations": conversations.filter(unread_count__gt=0).count(),
            "qualified_leads": leads.filter(status=DoubleTickLead.Status.QUALIFIED).count(),
            "distributed_leads": leads.filter(distributed_at__isnull=False).count(),
            "available_leads": leads.filter(status=DoubleTickLead.Status.AVAILABLE).count(),
            "claimed_leads": leads.filter(status=DoubleTickLead.Status.CLAIMED).count(),
            "contacted_leads": leads.filter(status=DoubleTickLead.Status.CONTACTED).count(),
            "booked_leads": leads.filter(status=DoubleTickLead.Status.BOOKED).count(),
            "lost_leads": leads.filter(status=DoubleTickLead.Status.LOST).count(),
            "average_claim_time": None,
        })


class DoubleTickWebhookView(APIView):
    """Public DoubleTick webhook endpoint protected by shared secret, not JWT."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if not is_valid_doubletick_webhook(request):
            return Response({"detail": "Invalid DoubleTick webhook secret."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DoubleTickWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead, webhook_log = create_or_update_lead_from_webhook(serializer.validated_data)
        return Response(
            {
                "status": "processed",
                "lead_id": str(lead.id) if lead else None,
                "conversation_id": str(webhook_log.conversation_id) if webhook_log.conversation_id else None,
                "webhook_log_id": str(webhook_log.id),
                "is_duplicate": bool(lead and lead.is_duplicate),
            },
            status=status.HTTP_201_CREATED,
        )

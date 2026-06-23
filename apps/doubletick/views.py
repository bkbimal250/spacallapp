import logging

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Q, Sum
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
from apps.locations.models import LocationGroupArea
from core.authentication import DeviceAuthentication

from .filters import DoubleTickConversationFilter, DoubleTickLeadFilter
from .models import (
    DoubleTickActivity,
    DoubleTickAreaAlias,
    DoubleTickConversation,
    DoubleTickDistributionAudit,
    DoubleTickLead,
    DoubleTickLeadActivity,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadAssignment,
    DoubleTickLeadVisibility,
    DoubleTickMessage,
    DoubleTickWebhookLog,
)
from .serializers import (
    DoubleTickActivitySerializer,
    DoubleTickAreaAliasSerializer,
    DoubleTickConversationAssignSupportSerializer,
    DoubleTickConversationDetailSerializer,
    DoubleTickConversationListSerializer,
    DoubleTickConversationMatchAreaSerializer,
    DoubleTickConversationReplySerializer,
    DoubleTickDistributionAuditSerializer,
    DoubleTickLeadActivitySerializer,
    DoubleTickLeadAreaBranchSerializer,
    DoubleTickLeadAreaSerializer,
    DoubleTickLeadAssignSerializer,
    DoubleTickLeadAssignmentSerializer,
    DoubleTickLeadDetailSerializer,
    DoubleTickLeadListSerializer,
    DoubleTickMobileLeadDetailSerializer,
    DoubleTickMobileLeadSerializer,
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


logger = logging.getLogger(__name__)


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


class DoubleTickDistributionAuditViewSet(DoubleTickAllListMixin, viewsets.ReadOnlyModelViewSet):
    """Admin-readable audit trail for DoubleTick lead distribution attempts."""

    serializer_class = DoubleTickDistributionAuditSerializer
    permission_classes = [IsInternalCRMTeam]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["lead", "conversation", "matched_area", "status"]
    search_fields = ["lead__phone_number", "lead__customer_name", "matched_area__name", "failure_reason"]
    ordering_fields = ["created_at", "mapped_branch_count", "visibility_count", "notification_success_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return DoubleTickDistributionAudit.objects.select_related("lead", "conversation", "matched_area")


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
    if auth and hasattr(auth, "device_id"):
        return auth
    if request.headers.get("X-Device-ID") or request.headers.get("X-Device-Secret"):
        authenticated = DeviceAuthentication().authenticate(request)
        return authenticated[0] if authenticated else None
    return None


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

    @action(detail=True, methods=["post"], permission_classes=[IsInternalCRMTeam], url_path="manual-correct")
    def manual_correct(self, request, pk=None):
        conversation = self.get_object()
        action_name = request.data.get("action")
        if not action_name:
            raise ValidationError({"action": "This field is required."})

        from apps.locations.models import Area, LocationGroup
        from apps.branches.models import Branch
        from apps.doubletick.models import DoubleTickAreaAlias, DoubleTickLeadArea, DoubleTickActivity
        from apps.doubletick.services import _activity, CRMLocationMatchEngine

        old_status = conversation.status

        if action_name == "correct_city":
            city_name = request.data.get("city_name")
            if not city_name:
                raise ValidationError({"city_name": "This field is required."})
            conversation.raw_city = city_name
            conversation.raw_area = ""
            conversation.matched_area = None
            conversation.area_confirmed = False
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
            conversation.requires_manual_attention = True
            conversation.save()

            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                old_status=old_status,
                new_status=conversation.status,
                note=f"Manually corrected as City: {city_name}",
                metadata={"action": action_name, "city_name": city_name, "method": "manual"}
            )

        elif action_name == "correct_group":
            group_name = request.data.get("group_name")
            if not group_name:
                raise ValidationError({"group_name": "This field is required."})

            group = LocationGroup.objects.filter(name__iexact=group_name, is_deleted=False, is_active=True).first()
            if group:
                conversation.raw_city = group.city.name
                payload = dict(conversation.raw_payload or {})
                payload["location_match"] = payload.get("location_match") or {}
                payload["location_match"]["raw_group"] = group.name
                conversation.raw_payload = payload

            conversation.raw_area = ""
            conversation.matched_area = None
            conversation.area_confirmed = False
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
            conversation.requires_manual_attention = True
            conversation.save()

            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                old_status=old_status,
                new_status=conversation.status,
                note=f"Manually corrected as Group: {group_name}",
                metadata={"action": action_name, "group_name": group_name, "method": "manual"}
            )

        elif action_name == "correct_area":
            area_id = request.data.get("area_id")
            if not area_id:
                raise ValidationError({"area_id": "This field is required."})
            area = Area.objects.filter(id=area_id, is_deleted=False, is_active=True).first()
            if not area:
                raise ValidationError({"area_id": "Area not found or inactive."})

            alias_text = str(request.data.get("alias_text") or "").strip()
            save_alias = bool(request.data.get("save_alias"))
            lead_area = CRMLocationMatchEngine.ensure_area_from_location_area(area)
            if save_alias and alias_text:
                DoubleTickAreaAlias.objects.get_or_create(
                    lead_area=lead_area,
                    normalized_alias=normalize_area_text(alias_text),
                    defaults={
                        "alias": alias_text,
                        "channel": conversation.channel,
                        "created_from_manual_mapping": True,
                    },
                )
                from apps.locations.services.fuzzy_matcher import clear_location_candidate_cache
                clear_location_candidate_cache()
            conversation.raw_city = area.city.name
            conversation.raw_area = area.name
            conversation.matched_area = lead_area
            conversation.area_confirmed = True
            conversation.status = DoubleTickConversation.Status.QUALIFIED
            conversation.pending_reason = ""
            conversation.requires_manual_attention = False
            conversation.save()

            if conversation.current_lead:
                LeadQualificationService.ensure_conversation_lead(conversation, distribute=False)

            _activity(
                conversation=conversation,
                lead=conversation.current_lead,
                action=DoubleTickActivity.Action.AREA_MATCHED,
                old_status=old_status,
                new_status=conversation.status,
                note=f"Manually corrected as Area: {area.name}",
                user=request.user,
                metadata={
                    "action": action_name,
                    "area_id": str(area.id),
                    "area_name": area.name,
                    "alias_saved": save_alias and bool(alias_text),
                    "original_text": alias_text,
                    "normalized_text": CRMLocationMatchEngine.normalize_text(alias_text),
                    "method": "manual",
                    "classification": "area",
                    "confidence": 1.0,
                    "applied": "yes",
                }
            )

        elif action_name == "correct_branch":
            branch_id = request.data.get("branch_id")
            if not branch_id:
                raise ValidationError({"branch_id": "This field is required."})
            branch = Branch.objects.filter(id=branch_id, is_deleted=False, is_active=True).first()
            if not branch:
                raise ValidationError({"branch_id": "Branch not found or inactive."})

            branch_area_text = branch.area or branch.spa_name
            lead_area = AreaMatchingService.ensure_area_from_branch(
                branch_area_text,
                branch.city,
                branch,
                conversation.channel
            )
            conversation.raw_city = branch.city
            conversation.raw_area = branch_area_text
            conversation.matched_area = lead_area
            conversation.area_confirmed = True
            conversation.status = DoubleTickConversation.Status.QUALIFIED
            conversation.pending_reason = ""
            conversation.requires_manual_attention = False
            conversation.save()

            if conversation.current_lead:
                lead = LeadQualificationService.ensure_conversation_lead(conversation, distribute=False)
                lead.current_branch = branch
                lead.assigned_branch = branch
                lead.save(update_fields=["current_branch", "assigned_branch", "updated_at"])

            _activity(
                conversation=conversation,
                lead=conversation.current_lead,
                action=DoubleTickActivity.Action.AREA_MATCHED,
                old_status=old_status,
                new_status=conversation.status,
                note=f"Manually corrected as Branch: {branch.spa_name}",
                metadata={"action": action_name, "branch_id": str(branch.id), "branch_name": branch.spa_name, "method": "manual"}
            )

        elif action_name == "add_alias":
            area_id = request.data.get("area_id")
            alias_text = request.data.get("alias_text")
            if not area_id or not alias_text:
                raise ValidationError({"area_id": "area_id and alias_text are required."})

            lead_area = DoubleTickLeadArea.objects.filter(id=area_id, is_active=True).first()
            if not lead_area:
                area = Area.objects.filter(id=area_id, is_deleted=False, is_active=True).first()
                if area:
                    lead_area = CRMLocationMatchEngine.ensure_area_from_location_area(area, channel=conversation.channel)
            if not lead_area:
                raise ValidationError({"area_id": "Lead area not found."})

            alias, created = DoubleTickAreaAlias.objects.get_or_create(
                lead_area=lead_area,
                normalized_alias=normalize_area_text(alias_text),
                defaults={"alias": alias_text, "channel": conversation.channel, "created_from_manual_mapping": True}
            )
            from apps.locations.services.fuzzy_matcher import clear_location_candidate_cache
            clear_location_candidate_cache()

            _activity(
                conversation=conversation,
                user=request.user,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                note=f"Added alias: {alias_text} -> {lead_area.name}",
                metadata={"action": action_name, "alias_text": alias_text, "lead_area_id": str(lead_area.id), "method": "manual"}
            )

        elif action_name == "mark_greeting":
            conversation.raw_area = ""
            conversation.matched_area = None
            conversation.area_confirmed = False
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.GREETING_ONLY
            conversation.requires_manual_attention = True
            conversation.save()

            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                old_status=old_status,
                new_status=conversation.status,
                note="Marked as Greeting",
                metadata={"action": action_name, "method": "manual"}
            )

        elif action_name == "mark_job":
            conversation.raw_area = ""
            conversation.matched_area = None
            conversation.area_confirmed = False
            conversation.status = DoubleTickConversation.Status.MANUAL_ATTENTION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MANUAL_REPLY_REQUIRED
            conversation.requires_manual_attention = True
            conversation.save()

            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                old_status=old_status,
                new_status=conversation.status,
                note="Marked as Job Inquiry",
                metadata={"action": action_name, "method": "manual"}
            )

        elif action_name == "mark_not_location":
            conversation.raw_area = ""
            conversation.matched_area = None
            conversation.area_confirmed = False
            conversation.status = DoubleTickConversation.Status.AWAITING_LOCATION
            conversation.pending_reason = DoubleTickConversation.PendingReason.MISSING_LOCATION
            conversation.requires_manual_attention = True
            conversation.save()

            _activity(
                conversation=conversation,
                action=DoubleTickActivity.Action.PENDING_REASON_UPDATED,
                old_status=old_status,
                new_status=conversation.status,
                note="Marked as Not Location",
                metadata={"action": action_name, "method": "manual"}
            )

        elif action_name == "save_and_send":
            if not conversation.area_confirmed or not conversation.matched_area_id:
                raise ValidationError("Cannot send to Android without a confirmed area match. Correct as Area or Branch first.")

            lead = LeadQualificationService.qualify_conversation(conversation, user=request.user, distribute=True)
            return Response(DoubleTickLeadDetailSerializer(lead).data)

        else:
            raise ValidationError({"action": "Unsupported manual correction action."})

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
    search_fields = [
        "customer_name",
        "phone_number",
        "latest_customer_message",
        "message",
        "raw_city",
        "raw_area",
        "matched_area__name",
        "doubletick_chat_id",
    ]
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

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        lead = self.get_object()
        text = request.data.get("text") or request.data.get("message") or ""
        if not text:
            raise ValidationError("Reply text is required.")
        from apps.bots.services import DoubleTickOutboundService

        message = DoubleTickOutboundService.send_text(
            lead.normalized_phone or lead.phone_number,
            lead.channel.waba_number if lead.channel else "",
            text,
            lead=lead,
            conversation=lead.conversation,
            origin=DoubleTickMessage.Origin.AGENT,
        )
        if lead.status in [DoubleTickLead.Status.CLAIMED, DoubleTickLead.Status.OPENED, DoubleTickLead.Status.CONTACTING, DoubleTickLead.Status.FOLLOW_UP]:
            lead.status = DoubleTickLead.Status.CONTACTED
            lead.contacted_at = timezone.now()
            lead.save(update_fields=["status", "contacted_at", "updated_at"])
        if lead.conversation_id:
            lead.conversation.last_agent_message_at = timezone.now()
            lead.conversation.team_last_replied_at = lead.conversation.last_agent_message_at
            lead.conversation.save(update_fields=["last_agent_message_at", "team_last_replied_at", "updated_at"])
        DoubleTickActivity.objects.create(lead=lead, conversation=lead.conversation, user=request.user, action=DoubleTickActivity.Action.MANUAL_REPLY_SENT, note=text)
        return Response(DoubleTickMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="send-location-options")
    def send_location_options(self, request, pk=None):
        lead = self.get_object()
        from apps.bots.services import BotEngine

        message = BotEngine.manual_send_location_options(lead)
        return Response(DoubleTickMessageSerializer(message).data if message else {"status": "no_options_sent"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def handover(self, request, pk=None):
        lead = self.get_object()
        lead.status = DoubleTickLead.Status.UNASSIGNED
        lead.remarks = "\n".join(part for part in [lead.remarks, request.data.get("reason", "Manual handover requested.")] if part)
        lead.save(update_fields=["status", "remarks", "updated_at"])
        if lead.conversation_id:
            lead.conversation.requires_manual_attention = True
            lead.conversation.status = DoubleTickConversation.Status.MANUAL_ATTENTION
            lead.conversation.pending_reason = DoubleTickConversation.PendingReason.MANUAL_REPLY_REQUIRED
            lead.conversation.save(update_fields=["requires_manual_attention", "status", "pending_reason", "updated_at"])
        DoubleTickActivity.objects.create(lead=lead, conversation=lead.conversation, user=request.user, action=DoubleTickActivity.Action.MANUAL_ATTENTION_REQUIRED)
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], url_path="run-bot-node")
    def run_bot_node(self, request, pk=None):
        serializer = __import__("apps.bots.serializers", fromlist=["BotRunNodeSerializer"]).BotRunNodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.bots.models import BotNode, BotSession
        from apps.bots.services import BotEngine

        lead = self.get_object()
        node = BotNode.objects.get(id=serializer.validated_data["node_id"])
        session = BotSession.objects.filter(lead=lead, status=BotSession.Status.ACTIVE).order_by("-updated_at").first()
        if not session:
            bot, flow = BotEngine.ensure_default_booking_bot()
            session = BotSession.objects.create(bot=bot, flow=flow, current_node=node, conversation=lead.conversation, customer=lead.customer, lead=lead)
        session.current_node = node
        session.save(update_fields=["current_node", "updated_at"])
        incoming = lead.messages.filter(direction=DoubleTickMessage.Direction.INBOUND).order_by("-created_at").first()
        BotEngine.run_current_node(session, incoming)
        return Response({"status": "node_run", "session_id": str(session.id)})

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
    serializer_class = DoubleTickMobileLeadSerializer

    def get_queryset(self):
        visible_rows = DoubleTickLeadVisibility.objects.filter(is_visible=True).select_related(
            "branch",
            "user",
            "device",
        )
        group_mappings = LocationGroupArea.objects.filter(
            is_deleted=False,
            group__is_deleted=False,
            group__is_active=True,
        ).select_related("group").order_by("priority", "group__priority", "group__name")
        queryset = DoubleTickLead.objects.select_related(
            "conversation",
            "matched_area",
            "matched_area__location_area",
            "matched_area__location_area__city",
            "current_branch",
            "current_user",
            "current_device",
            "active_assignment",
            "assigned_branch",
            "assigned_user",
            "assigned_device",
        ).prefetch_related(
            Prefetch("visibilities", queryset=visible_rows, to_attr="mobile_visibilities"),
            Prefetch(
                "matched_area__location_area__area_groups",
                queryset=group_mappings,
                to_attr="mobile_group_mappings",
            ),
        )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "messages",
                    queryset=DoubleTickMessage.objects.select_related("sent_by").order_by(
                        "message_timestamp",
                        "received_at",
                        "sent_at",
                        "created_at",
                    ),
                )
            )
        device = _device_from_request(self.request)
        if device:
            visibility_q = Q(visibilities__device=device, visibilities__is_visible=True) | Q(current_device=device)
            if device.branch_id:
                visibility_q |= Q(visibilities__branch=device.branch, visibilities__is_visible=True) | Q(current_branch=device.branch)
            queryset = queryset.filter(visibility_q).exclude(matched_area__isnull=True).distinct()
        else:
            queryset = _role_filtered_leads(queryset, self.request.user)
            if getattr(self.request.user, "role", None) not in ["super_admin", "admin", "area_manager"]:
                queryset = queryset.exclude(matched_area__isnull=True)

        params = self.request.query_params
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("unmatched", "").lower() == "true":
            queryset = queryset.filter(Q(matched_area__isnull=True) | Q(status=DoubleTickLead.Status.UNASSIGNED))
        if params.get("area_id"):
            queryset = queryset.filter(matched_area_id=params["area_id"])
        if params.get("branch_id"):
            queryset = queryset.filter(
                Q(current_branch_id=params["branch_id"])
                | Q(assigned_branch_id=params["branch_id"])
                | Q(visibilities__branch_id=params["branch_id"])
            )
        if params.get("area"):
            queryset = queryset.filter(Q(raw_area__icontains=params["area"]) | Q(matched_area__name__icontains=params["area"]))
        if params.get("city"):
            queryset = queryset.filter(Q(city__iexact=params["city"]) | Q(raw_city__iexact=params["city"]) | Q(matched_area__city__iexact=params["city"]))
        if params.get("location_status") == "matched":
            queryset = queryset.filter(matched_area__isnull=False)
        elif params.get("location_status") in ["pending", "unmatched"]:
            queryset = queryset.filter(Q(matched_area__isnull=True) | Q(status=DoubleTickLead.Status.UNASSIGNED))
        if params.get("search"):
            term = params["search"]
            queryset = queryset.filter(
                Q(customer_name__icontains=term)
                | Q(whatsapp_name__icontains=term)
                | Q(phone_number__icontains=term)
                | Q(normalized_phone__icontains=term)
                | Q(latest_customer_message__icontains=term)
                | Q(raw_area__icontains=term)
                | Q(matched_area__name__icontains=term)
            )
        if params.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=params["date_to"])
        if params.get("scope") == "my":
            if device:
                queryset = queryset.filter(current_device=device)
            else:
                queryset = queryset.filter(current_user=self.request.user)
        return queryset.order_by("-created_at").distinct()

    def get_serializer_class(self):
        return DoubleTickMobileLeadDetailSerializer if self.action == "retrieve" else DoubleTickMobileLeadSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["mobile_device"] = _device_from_request(self.request)
        context["request_user"] = self.request.user
        return context

    def _queue_response(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=["get"])
    def available(self, request):
        queryset = self.get_queryset().filter(status=DoubleTickLead.Status.AVAILABLE)
        return self._queue_response(queryset)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        device = _device_from_request(request)
        if device:
            queryset = self.get_queryset().filter(current_device=device)
        else:
            queryset = self.get_queryset().filter(current_user=request.user)
        return self._queue_response(queryset)

    @action(detail=False, methods=["get"])
    def claimed(self, request):
        queryset = self.get_queryset().filter(
            status__in=[
                DoubleTickLead.Status.CLAIMED,
                DoubleTickLead.Status.OPENED,
                DoubleTickLead.Status.CONTACTING,
                DoubleTickLead.Status.CONTACTED,
                DoubleTickLead.Status.FOLLOW_UP,
            ]
        )
        return self._queue_response(queryset)

    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        assignment = LeadClaimService.claim(pk, request.user, _device_from_request(request))
        return Response(DoubleTickLeadAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "open", request.data.get("note", ""), _device_from_request(request))
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"], url_path="start-contact")
    def start_contact(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "start_contact", request.data.get("note", ""), _device_from_request(request))
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        serializer = DoubleTickLeadStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_name = serializer.validated_data.get("action") or serializer.validated_data.get("status")
        lead = LeadClaimService.update_contact_status(pk, request.user, action_name, serializer.validated_data.get("note", ""), _device_from_request(request))
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"], url_path="follow-up")
    def follow_up(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "follow_up", request.data.get("note", ""), _device_from_request(request))
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        lead = LeadClaimService.release(pk, request.user, request.data.get("reason", ""), _device_from_request(request))
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"], url_path="add-remarks")
    def add_remarks(self, request, pk=None):
        lead = self.get_object()
        note = request.data.get("note") or request.data.get("remarks") or ""
        lead.remarks = "\n".join(part for part in [lead.remarks, note] if part)
        lead.save(update_fields=["remarks", "updated_at"])
        DoubleTickActivity.objects.create(lead=lead, user=request.user if request.user.is_authenticated else None, action=DoubleTickActivity.Action.STATUS_UPDATED, note=note)
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], url_path="send-reply")
    def send_reply(self, request, pk=None):
        lead = self.get_object()
        if not lead.conversation_id:
            raise ValidationError("Lead has no DoubleTick conversation.")
        text = request.data.get("text") or request.data.get("message") or ""
        if not text:
            raise ValidationError("Reply text is required.")
        message = DoubleTickReplyService.reply(lead.conversation, request.user, text)
        return Response(DoubleTickMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        lead = self.get_object()
        text = request.data.get("text") or request.data.get("message") or ""
        if not text:
            raise ValidationError("Reply text is required.")
        from apps.bots.services import DoubleTickOutboundService

        device = _device_from_request(request)
        message = DoubleTickOutboundService.send_text(
            lead.normalized_phone or lead.phone_number,
            lead.channel.waba_number if lead.channel else "",
            text,
            lead=lead,
            conversation=lead.conversation,
            origin=DoubleTickMessage.Origin.AGENT,
        )
        DoubleTickActivity.objects.create(
            lead=lead,
            conversation=lead.conversation,
            user=request.user if request.user.is_authenticated else None,
            device=device,
            action=DoubleTickActivity.Action.MANUAL_REPLY_SENT,
            note=text,
        )
        return Response(DoubleTickMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="send-location-options")
    def send_location_options(self, request, pk=None):
        lead = self.get_object()
        from apps.bots.services import BotEngine

        message = BotEngine.manual_send_location_options(lead)
        return Response(DoubleTickMessageSerializer(message).data if message else {"status": "no_options_sent"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def handover(self, request, pk=None):
        lead = self.get_object()
        lead.status = DoubleTickLead.Status.UNASSIGNED
        lead.save(update_fields=["status", "updated_at"])
        if lead.conversation_id:
            lead.conversation.requires_manual_attention = True
            lead.conversation.status = DoubleTickConversation.Status.MANUAL_ATTENTION
            lead.conversation.pending_reason = DoubleTickConversation.PendingReason.MANUAL_REPLY_REQUIRED
            lead.conversation.save(update_fields=["requires_manual_attention", "status", "pending_reason", "updated_at"])
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"], url_path="run-bot-node")
    def run_bot_node(self, request, pk=None):
        serializer = __import__("apps.bots.serializers", fromlist=["BotRunNodeSerializer"]).BotRunNodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.bots.models import BotNode, BotSession
        from apps.bots.services import BotEngine

        lead = self.get_object()
        node = BotNode.objects.get(id=serializer.validated_data["node_id"])
        session = BotSession.objects.filter(lead=lead, status=BotSession.Status.ACTIVE).order_by("-updated_at").first()
        if not session:
            bot, flow = BotEngine.ensure_default_booking_bot()
            session = BotSession.objects.create(bot=bot, flow=flow, current_node=node, conversation=lead.conversation, customer=lead.customer, lead=lead)
        session.current_node = node
        session.save(update_fields=["current_node", "updated_at"])
        incoming = lead.messages.filter(direction=DoubleTickMessage.Direction.INBOUND).order_by("-created_at").first()
        BotEngine.run_current_node(session, incoming)
        return Response({"status": "node_run", "session_id": str(session.id)})

    @action(detail=True, methods=["post"], url_path="mark-contacted")
    def mark_contacted(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "contacted", request.data.get("note", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def booked(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "booked", request.data.get("note", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def lost(self, request, pk=None):
        lead = LeadClaimService.update_contact_status(pk, request.user, "lost", request.data.get("note") or request.data.get("reason", ""), _device_from_request(request))
        return Response(DoubleTickLeadDetailSerializer(lead).data)


class DoubleTickDashboardMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        conversations = DoubleTickConversation.objects.all()
        leads = DoubleTickLead.objects.all()
        webhooks = DoubleTickWebhookLog.objects.all()
        messages = DoubleTickMessage.objects.all()
        return Response({
            "total_webhooks": webhooks.count(),
            "failed_webhooks": webhooks.filter(error_message__isnull=False).exclude(error_message="").count(),
            "incoming_messages": messages.filter(direction=DoubleTickMessage.Direction.INBOUND).count(),
            "outgoing_messages": messages.filter(direction=DoubleTickMessage.Direction.OUTBOUND).count(),
            "conversations": conversations.count(),
            "leads": leads.count(),
            "unmatched_leads": leads.filter(matched_area__isnull=True).count(),
            "matched_leads": leads.filter(matched_area__isnull=False).count(),
            "visibility_count": DoubleTickLeadVisibility.objects.count(),
            "distribution_failures": DoubleTickDistributionAudit.objects.filter(status=DoubleTickDistributionAudit.Status.FAILED).count(),
            "pending_manual_review": conversations.filter(requires_manual_attention=True).count(),
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
            "failed_distributions": DoubleTickDistributionAudit.objects.filter(status=DoubleTickDistributionAudit.Status.FAILED).count(),
            "partial_distributions": DoubleTickDistributionAudit.objects.filter(status=DoubleTickDistributionAudit.Status.PARTIAL).count(),
            "successful_distributions": DoubleTickDistributionAudit.objects.filter(status=DoubleTickDistributionAudit.Status.SUCCESS).count(),
            "notification_failures": DoubleTickDistributionAudit.objects.aggregate(
                total=Sum("notification_failure_count")
            )["total"] or 0,
            "average_claim_time": None,
        })


class DoubleTickWebhookView(APIView):
    """Public DoubleTick webhook endpoint protected by shared secret, not JWT."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if not is_valid_doubletick_webhook(request):
            return Response({"detail": "Invalid DoubleTick webhook secret."}, status=status.HTTP_403_FORBIDDEN)

        try:
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
        except Exception as exc:
            logger.exception("DoubleTick webhook processing failed.")
            webhook_log = DoubleTickWebhookLog.objects.create(
                event_type="processing_failed",
                payload=request.data if isinstance(request.data, dict) else {"raw": str(request.data)},
                processed=False,
                error_message=str(exc),
            )
            return Response(
                {"status": "accepted", "webhook_log_id": str(webhook_log.id), "error": "processing_failed"},
                status=status.HTTP_202_ACCEPTED,
            )

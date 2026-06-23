from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.doubletick.models import DoubleTickConversation, DoubleTickLead, DoubleTickMessage

from .models import (
    Bot,
    BotApiCallLog,
    BotDataSource,
    BotExecutionLog,
    BotFallbackRule,
    BotFlow,
    BotHandoverRule,
    BotIntegration,
    BotMessageTemplate,
    BotNode,
    BotNodeOption,
    BotSession,
    BotSessionVariable,
    BotSheetSyncLog,
    BotTransition,
    BotTrigger,
)
from .serializers import (
    BotApiCallLogSerializer,
    BotDataSourceSerializer,
    BotExecutionLogSerializer,
    BotFallbackRuleSerializer,
    BotFlowSerializer,
    BotHandoverRuleSerializer,
    BotIntegrationSerializer,
    BotMessageTemplateSerializer,
    BotNodeOptionSerializer,
    BotNodeSerializer,
    BotRunNodeSerializer,
    BotSerializer,
    BotSessionSerializer,
    BotSessionVariableSerializer,
    BotSheetSyncLogSerializer,
    BotTestFlowSerializer,
    BotTransitionSerializer,
    BotTriggerSerializer,
)
from .services import BotEngine, DoubleTickOutboundService


class IsBotAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) in ["super_admin", "admin"])


class BotAllListMixin:
    def list(self, request, *args, **kwargs):
        if request.query_params.get("all", "false").lower() == "true":
            self.pagination_class = None
        return super().list(request, *args, **kwargs)


class BotViewSet(BotAllListMixin, viewsets.ModelViewSet):
    serializer_class = BotSerializer
    permission_classes = [IsBotAdmin]
    queryset = Bot.objects.all().prefetch_related("flows", "triggers")

    @action(detail=True, methods=["post"], url_path="clone")
    def clone(self, request, pk=None):
        bot = self.get_object()
        clone = Bot.objects.create(
            name=request.data.get("name") or f"{bot.name} Copy",
            slug=request.data.get("slug") or f"{bot.slug}-copy-{Bot.objects.count() + 1}",
            bot_type=bot.bot_type,
            description=bot.description,
            default_language=bot.default_language,
            is_active=False,
            priority=bot.priority,
            config=bot.config,
        )
        return Response(BotSerializer(clone).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return Response({
            "total_bot_sessions": BotSession.objects.count(),
            "active_sessions": BotSession.objects.filter(status=BotSession.Status.ACTIVE).count(),
            "completed_sessions": BotSession.objects.filter(status=BotSession.Status.COMPLETED).count(),
            "handed_over_sessions": BotSession.objects.filter(status=BotSession.Status.HANDED_OVER).count(),
            "location_matched": BotSession.objects.exclude(selected_area="").count(),
            "unmatched": BotSession.objects.filter(selected_area="").count(),
            "bot_messages_sent": BotExecutionLog.objects.filter(status=BotExecutionLog.Status.SENT).count(),
            "manual_replies": DoubleTickMessage.objects.filter(direction=DoubleTickMessage.Direction.OUTBOUND, origin=DoubleTickMessage.Origin.AGENT).count(),
            "api_failures": BotApiCallLog.objects.filter(success=False).count(),
            "google_sheet_failures": BotSheetSyncLog.objects.filter(success=False).count(),
            "leads_by_city": list(DoubleTickLead.objects.values("city").annotate(total=Count("id")).order_by("city")),
            "leads_by_area": list(DoubleTickLead.objects.values("area").annotate(total=Count("id")).order_by("area")),
            "leads_by_branch": list(DoubleTickLead.objects.values("current_branch__spa_name").annotate(total=Count("id")).order_by("current_branch__spa_name")),
        })


class BotFlowViewSet(BotAllListMixin, viewsets.ModelViewSet):
    serializer_class = BotFlowSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotFlow.objects.select_related("bot").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        bot_id = self.request.query_params.get("bot")
        if bot_id:
            queryset = queryset.filter(bot_id=bot_id)
        return queryset

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        flow = self.get_object()
        flow.bot.flows.update(is_active=False)
        flow.is_active = True
        flow.is_published = True
        flow.published_at = timezone.now()
        flow.save()
        return Response(BotFlowSerializer(flow).data)


class BotNodeViewSet(BotAllListMixin, viewsets.ModelViewSet):
    serializer_class = BotNodeSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotNode.objects.select_related("flow", "default_next_node").prefetch_related("options").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        bot_id = self.request.query_params.get("bot")
        if bot_id:
            queryset = queryset.filter(flow__bot_id=bot_id)
        flow_id = self.request.query_params.get("flow")
        if flow_id:
            queryset = queryset.filter(flow_id=flow_id)
        return queryset

    @action(detail=True, methods=["post"], url_path="test")
    def test_node(self, request, pk=None):
        node = self.get_object()
        return Response({"node_id": str(node.id), "preview": node.message_text, "node_type": node.node_type, "config": node.config})


class BotNodeOptionViewSet(BotAllListMixin, viewsets.ModelViewSet):
    serializer_class = BotNodeOptionSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotNodeOption.objects.select_related("node", "next_node").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.query_params.get("node")
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        return queryset


class BotTransitionViewSet(BotAllListMixin, viewsets.ModelViewSet):
    serializer_class = BotTransitionSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotTransition.objects.select_related("flow", "from_node", "to_node").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        flow_id = self.request.query_params.get("flow")
        if flow_id:
            queryset = queryset.filter(flow_id=flow_id)
        return queryset


class BotTriggerViewSet(BotAllListMixin, viewsets.ModelViewSet):
    serializer_class = BotTriggerSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotTrigger.objects.select_related("bot", "channel", "branch").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        bot_id = self.request.query_params.get("bot")
        if bot_id:
            queryset = queryset.filter(bot_id=bot_id)
        return queryset


class BotSessionViewSet(BotAllListMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = BotSessionSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotSession.objects.select_related("bot", "flow", "current_node", "conversation", "lead", "selected_branch").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        bot_id = self.request.query_params.get("bot")
        if bot_id:
            queryset = queryset.filter(bot_id=bot_id)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class BotExecutionLogViewSet(BotAllListMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = BotExecutionLogSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotExecutionLog.objects.select_related("session", "node", "conversation", "lead", "incoming_message", "outbound_message").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        bot_id = self.request.query_params.get("bot")
        if bot_id:
            queryset = queryset.filter(session__bot_id=bot_id)
        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        node_id = self.request.query_params.get("node")
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        return queryset


class BotSimpleModelViewSet(BotAllListMixin, viewsets.ModelViewSet):
    permission_classes = [IsBotAdmin]


class BotMessageTemplateViewSet(BotSimpleModelViewSet):
    serializer_class = BotMessageTemplateSerializer
    queryset = BotMessageTemplate.objects.select_related("bot").all()


class BotDataSourceViewSet(BotSimpleModelViewSet):
    serializer_class = BotDataSourceSerializer
    queryset = BotDataSource.objects.all()


class BotIntegrationViewSet(BotSimpleModelViewSet):
    serializer_class = BotIntegrationSerializer
    queryset = BotIntegration.objects.all()


class BotApiCallLogViewSet(BotAllListMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = BotApiCallLogSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotApiCallLog.objects.select_related("integration", "session", "node").all()


class BotSheetSyncLogViewSet(BotAllListMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = BotSheetSyncLogSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotSheetSyncLog.objects.select_related("integration", "session", "lead").all()


class BotHandoverRuleViewSet(BotSimpleModelViewSet):
    serializer_class = BotHandoverRuleSerializer
    queryset = BotHandoverRule.objects.select_related("bot", "assign_user", "assign_branch").all()


class BotFallbackRuleViewSet(BotSimpleModelViewSet):
    serializer_class = BotFallbackRuleSerializer
    queryset = BotFallbackRule.objects.select_related("bot", "next_node").all()


class BotSessionVariableViewSet(BotAllListMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = BotSessionVariableSerializer
    permission_classes = [IsBotAdmin]
    queryset = BotSessionVariable.objects.select_related("session").all()


class BotTestFlowViewSet(viewsets.ViewSet):
    permission_classes = [IsBotAdmin]

    def create(self, request):
        serializer = BotTestFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = None
        lead = None
        if serializer.validated_data.get("lead_id"):
            lead = DoubleTickLead.objects.select_related("conversation", "customer").get(id=serializer.validated_data["lead_id"])
            conversation = lead.conversation
        elif serializer.validated_data.get("conversation_id"):
            conversation = DoubleTickConversation.objects.select_related("customer").get(id=serializer.validated_data["conversation_id"])
            lead = conversation.current_lead
        if not conversation:
            return Response({"detail": "conversation_id or lead_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        message = DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=lead,
            customer=conversation.customer,
            direction=DoubleTickMessage.Direction.INBOUND,
            origin=DoubleTickMessage.Origin.CUSTOMER,
            message_type="text",
            text=serializer.validated_data.get("text", "Hello"),
            customer_number=conversation.customer.phone_number,
            waba_number=conversation.channel.waba_number if conversation.channel else "",
            message_timestamp=timezone.now(),
            received_at=timezone.now(),
        )
        session = BotEngine.handle_incoming_message(conversation, lead, message)
        return Response(BotSessionSerializer(session).data if session else {"status": "no_session"})

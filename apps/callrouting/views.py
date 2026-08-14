from django.db.models import CharField, Count, Q
from django.db.models.functions import Cast
from django.utils.dateparse import parse_date
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.callrouting.models import RoutingRequest, RoutingRule, RoutingWhatsAppMessage
from apps.callrouting.serializers import RoutingRequestDetailSerializer, RoutingRequestListSerializer, RoutingRuleSerializer
from apps.common.utils import apply_branch_filter


class RoutingRequestViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RoutingRequestDetailSerializer
        return RoutingRequestListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RoutingRequest.objects.none()

        queryset = (
            RoutingRequest.objects.select_related(
                "call_log",
                "call_log__device",
                "contact",
                "lead",
                "routing_rule",
                "source_branch",
                "source_device",
            )
            .prefetch_related("candidates__branch", "attempts", "events", "whatsapp_messages")
            .order_by("-call_time", "-created_at")
        )
        queryset = apply_branch_filter(queryset, "source_branch_id", self.request.user)
        return self._apply_filters(queryset)

    def _apply_filters(self, queryset):
        params = self.request.query_params
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("routing_type"):
            queryset = queryset.filter(routing_type=params["routing_type"])
        if params.get("routing_rule"):
            queryset = queryset.filter(routing_rule_id=params["routing_rule"])
        if params.get("source_branch"):
            queryset = queryset.filter(source_branch_id=params["source_branch"])
        if params.get("source_branch_search"):
            term = params["source_branch_search"].strip()
            queryset = queryset.filter(
                Q(source_branch__spa_name__icontains=term)
                | Q(source_branch__code__icontains=term)
                | Q(source_branch__city__icontains=term)
                | Q(source_branch__area__icontains=term)
            )
        if params.get("city"):
            queryset = queryset.filter(source_branch__city__icontains=params["city"].strip())
        if params.get("area"):
            queryset = queryset.filter(source_branch__area__icontains=params["area"].strip())
        if params.get("whatsapp_status"):
            queryset = queryset.filter(whatsapp_messages__status=params["whatsapp_status"])

        date_value = parse_date(params.get("date") or "")
        if date_value:
            queryset = queryset.filter(call_time__date=date_value)
        date_from = parse_date(params.get("date_from") or "")
        if date_from:
            queryset = queryset.filter(call_time__date__gte=date_from)
        date_to = parse_date(params.get("date_to") or "")
        if date_to:
            queryset = queryset.filter(call_time__date__lte=date_to)

        search = params.get("search", "").strip()
        if search:
            queryset = queryset.annotate(
                routing_request_id_text=Cast("id", CharField()),
                call_log_id_text=Cast("call_log_id", CharField()),
            )
            queryset = queryset.filter(
                Q(normalized_phone__icontains=search)
                | Q(call_log__phone_number__icontains=search)
                | Q(contact__name__icontains=search)
                | Q(source_branch__spa_name__icontains=search)
                | Q(source_branch__code__icontains=search)
                | Q(call_log_id_text__icontains=search)
                | Q(routing_request_id_text__icontains=search)
            )

        return queryset.distinct()

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        totals = queryset.aggregate(
            total=Count("id"),
            routed=Count("id", filter=Q(status=RoutingRequest.Status.ROUTED)),
            skipped=Count("id", filter=Q(status=RoutingRequest.Status.SKIPPED)),
            failed=Count("id", filter=Q(status=RoutingRequest.Status.FAILED)),
            pending=Count("id", filter=Q(status=RoutingRequest.Status.PENDING)),
            whatsapp_queued=Count("whatsapp_messages", filter=Q(whatsapp_messages__status=RoutingWhatsAppMessage.Status.QUEUED)),
            whatsapp_sent=Count("whatsapp_messages", filter=Q(whatsapp_messages__status=RoutingWhatsAppMessage.Status.SENT)),
            whatsapp_delivered=Count("whatsapp_messages", filter=Q(whatsapp_messages__status=RoutingWhatsAppMessage.Status.DELIVERED)),
            whatsapp_failed=Count("whatsapp_messages", filter=Q(whatsapp_messages__status=RoutingWhatsAppMessage.Status.FAILED)),
        )
        total = totals["total"] or 0
        whatsapp_total = sum(
            totals[key] or 0
            for key in ["whatsapp_queued", "whatsapp_sent", "whatsapp_delivered", "whatsapp_failed"]
        )
        totals["routing_success_rate"] = round(((totals["routed"] or 0) / total) * 100, 2) if total else 0
        totals["whatsapp_delivery_rate"] = (
            round(((totals["whatsapp_delivered"] or 0) / whatsapp_total) * 100, 2) if whatsapp_total else 0
        )
        return Response(totals)


class RoutingRuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoutingRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = RoutingRule.objects.all().order_by("priority", "name")

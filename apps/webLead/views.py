from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils import apply_branch_filter

from . import analytics
from .filters import WebsiteFormConfigurationFilter, WebsiteLeadFilter
from .models import (
    WebsiteFormConfiguration,
    WebsiteLead,
    WebsiteLeadNotificationStatus,
    WebsiteLeadRoutingStatus,
)
from .permissions import IsAdminOrSuperAdmin, IsWebLeadConfigurationUser, IsWebLeadUser
from .serializers import (
    PublicWebsiteFormConfigSerializer,
    WebsiteFormConfigurationSerializer,
    WebsiteLeadAssignSerializer,
    WebsiteLeadDetailSerializer,
    WebsiteLeadListSerializer,
    WebsiteLeadSubmitSerializer,
    WebsiteLeadUpdateSerializer,
)
from .services import (
    create_website_lead_from_submission,
    get_client_ip,
    record_website_lead_activity,
    send_website_lead_notification,
)
from .validators import validate_form_key


class PublicSubmitRateLimitMixin:
    rate_limit = 30
    rate_window_seconds = 60

    def check_rate_limit(self, request):
        ip_address = get_client_ip(request) or "unknown"
        cache_key = f"web_lead_submit_rate:{ip_address}"
        count = cache.get(cache_key, 0)
        if count >= self.rate_limit:
            return False
        cache.set(cache_key, count + 1, self.rate_window_seconds)
        return True


class WebsiteFormConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = WebsiteFormConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated, IsWebLeadConfigurationUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WebsiteFormConfigurationFilter
    search_fields = ["website_name", "website_url", "form_key", "branch__spa_name"]
    ordering_fields = ["created_at", "updated_at", "website_name", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WebsiteFormConfiguration.objects.none()
        qs = WebsiteFormConfiguration.objects.select_related("branch", "created_by").all()
        return apply_branch_filter(qs, "branch_id", self.request.user, self.request.query_params.get("branch"))

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        record_website_lead_activity(
            "form_configuration_created",
            form_configuration=instance,
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        old_active = serializer.instance.is_active
        instance = serializer.save()
        action = "form_configuration_updated"
        if old_active != instance.is_active:
            action = "form_activated" if instance.is_active else "form_deactivated"
        record_website_lead_activity(
            action,
            form_configuration=instance,
            created_by=self.request.user,
        )


class PublicWebsiteFormConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, form_key):
        form_key = validate_form_key(form_key)
        config = get_object_or_404(WebsiteFormConfiguration, form_key=form_key)
        return Response(PublicWebsiteFormConfigSerializer(config).data)


class WebsiteLeadSubmitView(PublicSubmitRateLimitMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not self.check_rate_limit(request):
            return Response(
                {"success": False, "message": "Please wait before submitting again."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        serializer = WebsiteLeadSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = create_website_lead_from_submission(serializer.validated_data, request=request)
        return Response(
            {
                "success": True,
                "message": lead.form_configuration.success_message
                if lead.form_configuration
                else "Thank you. Our team will contact you shortly.",
                "lead_id": str(lead.id),
            },
            status=status.HTTP_201_CREATED,
        )


class WebsiteLeadViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsWebLeadUser]
    http_method_names = ["get", "patch", "head", "options"]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WebsiteLeadFilter
    search_fields = ["customer_name", "phone", "address", "website_name", "form_key"]
    ordering_fields = ["created_at", "updated_at", "status", "website_name"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return WebsiteLeadListSerializer
        if self.action in ["update", "partial_update"]:
            return WebsiteLeadUpdateSerializer
        return WebsiteLeadDetailSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WebsiteLead.objects.none()
        qs = WebsiteLead.objects.select_related(
            "branch", "form_configuration", "assigned_to"
        ).all()
        user = self.request.user
        if getattr(user, "role", None) in ["super_admin", "admin"]:
            return apply_branch_filter(qs, "branch_id", user, self.request.query_params.get("branch"))
        return apply_branch_filter(qs.exclude(branch__isnull=True), "branch_id", user)

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        instance = serializer.save()
        if old_status != instance.status:
            record_website_lead_activity(
                "lead_status_changed",
                lead=instance,
                old_value=old_status,
                new_value=instance.status,
                created_by=self.request.user,
            )


class WebsiteLeadAssignView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, pk):
        lead = get_object_or_404(WebsiteLead, pk=pk)
        serializer = WebsiteLeadAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_branch = lead.branch_id
        lead.branch = serializer.validated_data["branch"]
        lead.assigned_to = serializer.validated_data.get("assigned_to")
        lead.routing_status = WebsiteLeadRoutingStatus.ROUTED
        lead.notification_status = WebsiteLeadNotificationStatus.PENDING
        lead.save(update_fields=["branch", "assigned_to", "routing_status", "notification_status", "updated_at"])
        record_website_lead_activity(
            "pending_lead_manually_assigned",
            lead=lead,
            old_value=old_branch,
            new_value=lead.branch_id,
            created_by=request.user,
        )
        send_website_lead_notification(lead)
        return Response(WebsiteLeadDetailSerializer(lead).data, status=status.HTTP_200_OK)


class _AnalyticsBaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, request):
        qs = WebsiteLead.objects.select_related("branch").all()
        return apply_branch_filter(qs, "branch_id", request.user, request.query_params.get("branch"))


class WebsiteLeadAnalyticsOverviewView(_AnalyticsBaseView):
    def get(self, request):
        return Response(analytics.overview(self.get_queryset(request)))


class WebsiteLeadBranchAnalyticsView(_AnalyticsBaseView):
    def get(self, request):
        return Response(analytics.branch_analytics(self.get_queryset(request)))


class WebsiteLeadWebsiteAnalyticsView(_AnalyticsBaseView):
    def get(self, request):
        return Response(analytics.website_analytics(self.get_queryset(request)))


class WebsiteLeadFormAnalyticsView(_AnalyticsBaseView):
    def get(self, request):
        return Response(analytics.form_analytics(self.get_queryset(request)))


class WidgetScriptView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.contrib.staticfiles import finders

        path = finders.find("webLead/widget.js")
        if not path:
            return Response({"detail": "Widget script not found."}, status=status.HTTP_404_NOT_FOUND)
        with open(path, "r", encoding="utf-8") as widget_file:
            return HttpResponse(widget_file.read(), content_type="application/javascript")

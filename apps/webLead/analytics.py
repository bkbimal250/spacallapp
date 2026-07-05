from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone

from .models import WebsiteLead, WebsiteLeadNotificationStatus, WebsiteLeadStatus


def _period_filters():
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "today": Q(created_at__gte=today),
        "weekly": Q(created_at__gte=now - timedelta(days=7)),
        "monthly": Q(created_at__gte=now - timedelta(days=30)),
    }


def overview(queryset=None):
    qs = queryset or WebsiteLead.objects.all()
    periods = _period_filters()
    return qs.aggregate(
        total_website_leads=Count("id"),
        today_website_leads=Count("id", filter=periods["today"]),
        weekly_website_leads=Count("id", filter=periods["weekly"]),
        monthly_website_leads=Count("id", filter=periods["monthly"]),
        duplicate_leads=Count("id", filter=Q(status=WebsiteLeadStatus.DUPLICATE)),
        pending_unassigned_leads=Count("id", filter=Q(branch__isnull=True)),
        converted_leads=Count("id", filter=Q(status=WebsiteLeadStatus.CONVERTED)),
        rejected_leads=Count("id", filter=Q(status=WebsiteLeadStatus.REJECTED)),
    )


def branch_analytics(queryset=None):
    qs = queryset or WebsiteLead.objects.all()
    periods = _period_filters()
    return list(
        qs.values("branch_id", "branch__spa_name")
        .annotate(
            total_leads=Count("id"),
            today_leads=Count("id", filter=periods["today"]),
            weekly_leads=Count("id", filter=periods["weekly"]),
            monthly_leads=Count("id", filter=periods["monthly"]),
            converted_leads=Count("id", filter=Q(status=WebsiteLeadStatus.CONVERTED)),
            rejected_leads=Count("id", filter=Q(status=WebsiteLeadStatus.REJECTED)),
            duplicate_leads=Count("id", filter=Q(status=WebsiteLeadStatus.DUPLICATE)),
            notification_sent_count=Count(
                "id", filter=Q(notification_status=WebsiteLeadNotificationStatus.SENT)
            ),
            notification_failed_count=Count(
                "id", filter=Q(notification_status=WebsiteLeadNotificationStatus.FAILED)
            ),
        )
        .order_by("branch__spa_name")
    )


def website_analytics(queryset=None):
    qs = queryset or WebsiteLead.objects.all()
    periods = _period_filters()
    return list(
        qs.values("branch_id", "branch__spa_name", "website_name", "website_url")
        .annotate(
            total_leads=Count("id"),
            today_leads=Count("id", filter=periods["today"]),
            weekly_leads=Count("id", filter=periods["weekly"]),
            monthly_leads=Count("id", filter=periods["monthly"]),
            converted_leads=Count("id", filter=Q(status=WebsiteLeadStatus.CONVERTED)),
            rejected_leads=Count("id", filter=Q(status=WebsiteLeadStatus.REJECTED)),
            duplicate_leads=Count("id", filter=Q(status=WebsiteLeadStatus.DUPLICATE)),
            last_lead_received_at=Max("created_at"),
        )
        .order_by("branch__spa_name", "website_name")
    )


def form_analytics(queryset=None):
    qs = queryset or WebsiteLead.objects.all()
    return list(
        qs.values("branch_id", "branch__spa_name", "website_name", "website_url", "form_key")
        .annotate(
            total_leads=Count("id"),
            successful_submissions=Count(
                "id",
                filter=~Q(status__in=[WebsiteLeadStatus.DUPLICATE, WebsiteLeadStatus.REJECTED]),
            ),
            duplicate_submissions=Count("id", filter=Q(status=WebsiteLeadStatus.DUPLICATE)),
            rejected_submissions=Count("id", filter=Q(status=WebsiteLeadStatus.REJECTED)),
            last_submitted_at=Max("created_at"),
        )
        .order_by("branch__spa_name", "website_name", "form_key")
    )

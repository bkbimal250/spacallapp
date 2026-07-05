import logging
import secrets
import re
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify

from apps.notifications.services import NotificationService

from .models import (
    WebsiteFormConfiguration,
    WebsiteFormDailyStats,
    WebsiteLead,
    WebsiteLeadActivity,
    WebsiteLeadNotificationStatus,
    WebsiteLeadRoutingStatus,
    WebsiteLeadStatus,
)
from .validators import normalize_phone, sanitize_text

logger = logging.getLogger(__name__)


def generate_form_key(website_name=None):
    base = slugify(website_name or "website").replace("-", "_")[:24] or "website"
    while True:
        suffix = secrets.randbelow(900000) + 100000
        form_key = f"frm_{base}_{suffix}".lower()
        if not WebsiteFormConfiguration.objects.filter(form_key=form_key).exists():
            return form_key


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def detect_duplicate_lead(phone, form_key):
    since = timezone.now() - timedelta(hours=24)
    return WebsiteLead.objects.filter(
        phone=phone,
        form_key=form_key,
        created_at__gte=since,
    ).exists()


def route_lead_to_branch(lead):
    if lead.branch_id:
        lead.routing_status = WebsiteLeadRoutingStatus.ROUTED
    elif lead.form_configuration_id:
        lead.routing_status = WebsiteLeadRoutingStatus.PENDING_CONFIGURATION
    else:
        lead.routing_status = WebsiteLeadRoutingStatus.UNASSIGNED
    return lead


def record_website_lead_activity(
    action,
    lead=None,
    form_configuration=None,
    old_value="",
    new_value="",
    message="",
    created_by=None,
    metadata=None,
):
    return WebsiteLeadActivity.objects.create(
        lead=lead,
        form_configuration=form_configuration,
        action=action,
        old_value=str(old_value or ""),
        new_value=str(new_value or ""),
        message=message or "",
        created_by=created_by if getattr(created_by, "is_authenticated", False) else None,
        metadata=metadata or {},
    )


def update_web_lead_analytics(lead):
    date = timezone.localdate(lead.created_at)
    stats, _ = WebsiteFormDailyStats.objects.get_or_create(
        date=date,
        branch=lead.branch,
        form_key=lead.form_key,
        defaults={
            "website_name": lead.website_name,
            "website_url": lead.website_url,
        },
    )
    updates = {"total_submissions": F("total_submissions") + 1}
    if lead.status == WebsiteLeadStatus.DUPLICATE:
        updates["duplicate_submissions"] = F("duplicate_submissions") + 1
    elif lead.status == WebsiteLeadStatus.REJECTED:
        updates["rejected_submissions"] = F("rejected_submissions") + 1
    else:
        updates["successful_submissions"] = F("successful_submissions") + 1
    if lead.status == WebsiteLeadStatus.CONVERTED:
        updates["converted_count"] = F("converted_count") + 1
    if lead.notification_status == WebsiteLeadNotificationStatus.SENT:
        updates["notification_sent_count"] = F("notification_sent_count") + 1
    if lead.notification_status == WebsiteLeadNotificationStatus.FAILED:
        updates["notification_failed_count"] = F("notification_failed_count") + 1

    WebsiteFormDailyStats.objects.filter(pk=stats.pk).update(**updates)


def _branch_notification_recipients(branch):
    if not branch:
        return []
    return list(
        branch.branch_users.filter(
            is_active=True,
            role__in=["spa_manager", "area_manager", "admin", "super_admin"],
        ).exclude(fcm_token__isnull=True).exclude(fcm_token="")
    )


def send_website_lead_notification(lead):
    if lead.routing_status != WebsiteLeadRoutingStatus.ROUTED or not lead.branch_id:
        lead.notification_status = WebsiteLeadNotificationStatus.NOT_REQUIRED
        lead.save(update_fields=["notification_status", "updated_at"])
        record_website_lead_activity("notification_not_required", lead=lead)
        return False

    recipients = _branch_notification_recipients(lead.branch)
    if not recipients:
        lead.notification_status = WebsiteLeadNotificationStatus.FAILED
        lead.notification_error = "No active branch user with FCM token."
        lead.save(update_fields=["notification_status", "notification_error", "updated_at"])
        record_website_lead_activity(
            "notification_failed",
            lead=lead,
            message=lead.notification_error,
        )
        return False

    payload = {
        "lead_id": str(lead.id),
        "lead_type": "website_lead",
        "branch_id": str(lead.branch_id),
        "website_name": lead.website_name,
        "form_key": lead.form_key,
    }
    body = f"{lead.customer_name} - {lead.phone} from {lead.website_name}"
    sent_any = False
    errors = []
    for recipient in recipients:
        try:
            sent_any = NotificationService.send_push(
                recipient=recipient,
                title="New Website Lead",
                body=body,
                notification_type="alert",
                data=payload,
            ) or sent_any
        except Exception as exc:
            logger.exception("Website lead FCM notification failed")
            errors.append(str(exc))

    lead.notification_status = (
        WebsiteLeadNotificationStatus.SENT if sent_any else WebsiteLeadNotificationStatus.FAILED
    )
    lead.notification_error = "" if sent_any else "; ".join(errors) or "Notification send failed."
    lead.save(update_fields=["notification_status", "notification_error", "updated_at"])
    record_website_lead_activity(
        "notification_sent" if sent_any else "notification_failed",
        lead=lead,
        message=lead.notification_error,
    )
    return sent_any


def create_website_lead_from_submission(validated_data, request=None):
    form_key = validated_data["form_key"]
    config = WebsiteFormConfiguration.objects.select_related("branch").get(form_key=form_key)
    phone = normalize_phone(validated_data["phone"])
    is_duplicate = detect_duplicate_lead(phone, form_key)

    with transaction.atomic():
        lead = WebsiteLead(
            form_configuration=config,
            branch=config.branch,
            website_name=config.website_name,
            website_url=config.website_url,
            form_key=config.form_key,
            customer_name=sanitize_text(validated_data["name"]),
            phone=phone,
            address=sanitize_text(validated_data["address"]),
            notes=sanitize_text(validated_data.get("notes", "")),
            submitted_from_url=validated_data.get("submitted_from_url", "") or "",
            referrer_url=(request.META.get("HTTP_REFERER", "") if request else ""),
            ip_address=get_client_ip(request) if request else None,
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:2000] if request else ""),
            status=WebsiteLeadStatus.DUPLICATE if is_duplicate else WebsiteLeadStatus.NEW,
            notification_status=WebsiteLeadNotificationStatus.PENDING,
        )
        route_lead_to_branch(lead)
        if lead.routing_status != WebsiteLeadRoutingStatus.ROUTED:
            lead.notification_status = WebsiteLeadNotificationStatus.NOT_REQUIRED
        lead.save()
        record_website_lead_activity(
            "website_lead_submitted",
            lead=lead,
            form_configuration=config,
            metadata={"duplicate": is_duplicate},
        )

    if lead.routing_status == WebsiteLeadRoutingStatus.ROUTED:
        send_website_lead_notification(lead)
    update_web_lead_analytics(lead)
    return lead

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from .models import DeviceComplianceState
from .services import MonitoringAlertService


DOWNLOAD_URL = "https://mastercall.in/download"
UPDATE_TITLE = "App Update Required"
UPDATE_BODY = (
    "Your MasterCall app registration is incomplete. Please update/reinstall "
    "the app to continue receiving leads and notifications.\n\n"
    f"Download: {DOWNLOAD_URL}"
)


class DeviceComplianceService:
    OK = "OK"
    MISSING_ANDROID_ID = "MISSING_ANDROID_ID"
    MISSING_FCM_TOKEN = "MISSING_FCM_TOKEN"
    OUTDATED_APP = "OUTDATED_APP"
    HEARTBEAT_MISSING = "HEARTBEAT_MISSING"
    SUSPECTED_UNINSTALLED = "SUSPECTED_UNINSTALLED"
    AUTH_BROKEN = "AUTH_BROKEN"

    @staticmethod
    def state_for(device):
        state, _ = DeviceComplianceState.objects.get_or_create(device=device)
        return state

    @staticmethod
    def check_device(device):
        state = DeviceComplianceService.state_for(device)
        health = getattr(device, "health", None)
        now = timezone.now()

        status = DeviceComplianceService.OK
        reason = "Device compliance is OK."

        missing_credentials = not device.is_registered or not device.device_id or not device.secret_key
        if missing_credentials:
            status = DeviceComplianceService.AUTH_BROKEN
            reason = "Device registration is incomplete or missing credentials."
        elif not device.is_active or device.is_blocked:
            status = DeviceComplianceService.AUTH_BROKEN
            reason = "Device is inactive or blocked."
        elif not device.android_id:
            status = DeviceComplianceService.MISSING_ANDROID_ID
            reason = "Device is registered but Android ID is missing."
        elif state.fcm_invalid or not device.fcm_token:
            status = DeviceComplianceService.MISSING_FCM_TOKEN
            reason = "Device FCM token is missing or invalid."
        elif not device.last_heartbeat:
            status = DeviceComplianceService.HEARTBEAT_MISSING
            reason = "Device has never sent a heartbeat."
        else:
            heartbeat_missing_after = timedelta(
                minutes=getattr(settings, "MONITORING_OFFLINE_AFTER_MINUTES", 20)
            )
            suspected_after = timedelta(
                hours=getattr(settings, "MONITORING_UNINSTALL_SUSPECT_AFTER_HOURS", 24)
            )
            age = now - device.last_heartbeat
            if age >= suspected_after:
                status = DeviceComplianceService.SUSPECTED_UNINSTALLED
                reason = "No heartbeat for a long time; app may be uninstalled, force-stopped, or offline."
            elif age >= heartbeat_missing_after:
                status = DeviceComplianceService.HEARTBEAT_MISSING
                reason = "Device heartbeat is missing."
            else:
                min_version = getattr(settings, "MASTERCALL_MIN_ANDROID_APP_VERSION", "")
                app_version = getattr(health, "app_version", None)
                if min_version and app_version and app_version < min_version:
                    status = DeviceComplianceService.OUTDATED_APP
                    reason = f"App version {app_version} is older than required {min_version}."

        if state.status != status or state.reason != reason:
            state.status = status
            state.reason = reason
            state.save(update_fields=["status", "reason", "updated_at"])
        return status, reason, state

    @staticmethod
    def mark_fcm_invalid(device, reason="FCM token is invalid or not registered."):
        state = DeviceComplianceService.state_for(device)
        state.fcm_invalid = True
        state.status = DeviceComplianceService.SUSPECTED_UNINSTALLED
        state.reason = reason
        state.save(update_fields=["fcm_invalid", "status", "reason", "updated_at"])
        DeviceComplianceService.create_crm_alert(device, state.status, reason)
        DeviceComplianceService.send_admin_email(device, state.status, reason)

    @staticmethod
    def mark_fcm_valid(device):
        state = DeviceComplianceService.state_for(device)
        if state.fcm_invalid:
            state.fcm_invalid = False
            if state.status in (
                DeviceComplianceService.MISSING_FCM_TOKEN,
                DeviceComplianceService.SUSPECTED_UNINSTALLED,
            ):
                state.status = DeviceComplianceService.OK
                state.reason = "FCM token refreshed by device."
                state.save(update_fields=["fcm_invalid", "status", "reason", "updated_at"])
            else:
                state.save(update_fields=["fcm_invalid", "updated_at"])
        return state

    @staticmethod
    def can_send_phone_notification(state, now=None):
        now = now or timezone.now()
        return not state.last_phone_notification_at or state.last_phone_notification_at <= now - timedelta(hours=1)

    @staticmethod
    def send_update_notification(device, state=None, force=False):
        state = state or DeviceComplianceService.state_for(device)
        if state.fcm_invalid or not device.fcm_token:
            return False, "missing_or_invalid_fcm"
        if not force and not DeviceComplianceService.can_send_phone_notification(state):
            return False, "cooldown"

        sent = NotificationService.send_push(
            recipient=device,
            title=UPDATE_TITLE,
            body=UPDATE_BODY,
            notification_type="alert",
            data={
                "source": "device_compliance",
                "action": "update_app",
                "action_url": DOWNLOAD_URL,
                "action_label": "Update App",
                "download_url": DOWNLOAD_URL,
                "compliance_status": state.status,
                "high_priority": "true",
            },
        )
        if sent:
            state.last_phone_notification_at = timezone.now()
            state.save(update_fields=["last_phone_notification_at", "updated_at"])
            return True, "sent"
        return False, "send_failed"

    @staticmethod
    def create_crm_alert(device, status, reason):
        state = DeviceComplianceService.state_for(device)
        now = timezone.now()
        if state.last_admin_alert_at and state.last_admin_alert_at > now - timedelta(hours=1):
            return 0

        User = get_user_model()
        admins = User.objects.filter(is_active=True, role__in=["super_admin", "admin"])
        branch_name = device.branch.spa_name if device.branch else "Unassigned"
        body = (
            "Branch/user device is suspected uninstalled or inactive. Kindly follow up with this branch/user "
            "and ask them to update the app.\n\n"
            f"Branch: {branch_name}\n"
            f"Phone: {device.phone_name or '-'}\n"
            f"Device ID: {device.device_id or '-'}\n"
            f"Android ID: {device.android_id or '-'}\n"
            f"App Version: {getattr(getattr(device, 'health', None), 'app_version', '-')}\n"
            f"Last Seen: {device.last_heartbeat or '-'}\n"
            f"Issue Reason: {status} - {reason}\n"
            f"Download Link: {DOWNLOAD_URL}"
        )
        created = 0
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Device App Alert",
                body=body,
                notification_type="alert",
            )
            created += 1

        MonitoringAlertService.raise_event(
            device=device,
            event_type="app_uninstall_suspected" if status == DeviceComplianceService.SUSPECTED_UNINSTALLED else "permission_denied",
            description=f"{status}: {reason}",
            notify=False,
        )
        state.last_admin_alert_at = now
        state.save(update_fields=["last_admin_alert_at", "updated_at"])
        return created

    @staticmethod
    def send_admin_email(device, status, reason):
        state = DeviceComplianceService.state_for(device)
        now = timezone.now()
        cooldown_minutes = getattr(settings, "DEVICE_COMPLIANCE_ADMIN_EMAIL_COOLDOWN_MINUTES", 60)
        if state.last_admin_email_at and state.last_admin_email_at > now - timedelta(minutes=cooldown_minutes):
            return 0

        User = get_user_model()
        recipients = list(
            User.objects.filter(is_active=True, role__in=["super_admin", "admin"])
            .exclude(email="")
            .values_list("email", flat=True)
        )
        recipients.extend(getattr(settings, "DEVICE_COMPLIANCE_ADMIN_EMAILS", []))
        recipients = sorted(set(filter(None, recipients)))
        if not recipients:
            return 0

        branch_name = device.branch.spa_name if device.branch else "Unassigned"
        body = (
            "This branch/user device is suspected uninstalled or has broken app registration. Kindly take follow-up.\n\n"
            f"Branch: {branch_name}\n"
            f"User/Phone: {device.phone_name or '-'}\n"
            f"Device ID: {device.device_id or '-'}\n"
            f"Android ID: {device.android_id or '-'}\n"
            f"FCM Status: {'invalid/missing' if state.fcm_invalid or not device.fcm_token else 'present'}\n"
            f"Last Seen: {device.last_heartbeat or '-'}\n"
            f"Issue Reason: {status} - {reason}\n"
            f"Download Link: {DOWNLOAD_URL}"
        )
        send_mail(
            subject="MasterCall Device Alert: App Missing/Uninstalled Suspected",
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=recipients,
            fail_silently=False,
        )
        state.last_admin_email_at = now
        state.save(update_fields=["last_admin_email_at", "updated_at"])
        return len(recipients)

    @staticmethod
    def mark_followed_up(device):
        state = DeviceComplianceService.state_for(device)
        state.followed_up_at = timezone.now()
        state.save(update_fields=["followed_up_at", "updated_at"])
        return state

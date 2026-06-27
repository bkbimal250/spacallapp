from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from apps.devices.models import Device
from apps.monitoring.compliance import DeviceComplianceService


class Command(BaseCommand):
    help = "Check registered devices for compliance issues and send safe hourly alerts."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--dry-run", action="store_true", help="Only print what would be sent.")
        mode.add_argument("--commit", action="store_true", help="Send notifications and admin alerts.")

    def handle(self, *args, **options):
        if options["dry_run"] and options["commit"]:
            raise CommandError("Choose only one mode.")

        commit = options["commit"]
        report = Counter()
        errors = []

        queryset = (
            Device.objects.filter(is_registered=True, is_deleted=False)
            .select_related("branch", "health", "compliance_state")
            .order_by("branch__spa_name", "device_id")
        )
        report["total_checked"] = queryset.count()

        admin_statuses = {
            DeviceComplianceService.MISSING_ANDROID_ID,
            DeviceComplianceService.MISSING_FCM_TOKEN,
            DeviceComplianceService.HEARTBEAT_MISSING,
            DeviceComplianceService.DEVICE_TIME_WRONG,
            DeviceComplianceService.SUSPECTED_UNINSTALLED,
            DeviceComplianceService.AUTH_BROKEN,
        }

        for device in queryset:
            try:
                status, reason, state = DeviceComplianceService.check_device(device)
                report[status.lower()] += 1
                if status == DeviceComplianceService.OK:
                    continue

                if DeviceComplianceService.can_send_phone_notification(state):
                    if commit:
                        sent, result = DeviceComplianceService.send_update_notification(device, state=state)
                        if sent:
                            report["notifications_sent"] += 1
                        elif result == "cooldown":
                            report["skipped_cooldown"] += 1
                        elif result == "missing_or_invalid_fcm":
                            report["missing_fcm_token"] += 1
                        else:
                            report["notification_errors"] += 1
                    else:
                        report["notification_would_send"] += 1
                else:
                    report["skipped_cooldown"] += 1

                if status in admin_statuses:
                    if commit:
                        report["crm_alerts_sent"] += DeviceComplianceService.create_crm_alert(device, status, reason)
                        report["admin_emails_sent"] += DeviceComplianceService.send_admin_email(device, status, reason)
                    else:
                        report["crm_alerts_would_send"] += 1
                        report["email_alerts_would_send"] += 1
            except Exception as exc:
                report["errors"] += 1
                errors.append(f"{device.device_id or device.id}: {exc}")

        self.stdout.write("Device compliance alert report")
        self.stdout.write(f"Mode: {'commit' if commit else 'dry-run'}")
        labels = [
            ("total checked", "total_checked"),
            ("notifications sent", "notifications_sent"),
            ("notifications would send", "notification_would_send"),
            ("skipped cooldown", "skipped_cooldown"),
            ("missing android_id", "missing_android_id"),
            ("missing fcm token", "missing_fcm_token"),
            ("heartbeat missing", "heartbeat_missing"),
            ("suspected uninstalled", "suspected_uninstalled"),
            ("auth broken", "auth_broken"),
            ("outdated app", "outdated_app"),
            ("crm alerts sent", "crm_alerts_sent"),
            ("crm alerts would send", "crm_alerts_would_send"),
            ("admin emails sent", "admin_emails_sent"),
            ("admin emails would send", "email_alerts_would_send"),
            ("notification errors", "notification_errors"),
            ("errors", "errors"),
        ]
        for label, key in labels:
            self.stdout.write(f"{label}: {report[key]}")

        for error in errors[:20]:
            self.stderr.write(error)

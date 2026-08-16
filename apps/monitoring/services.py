import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.notifications.services import NotificationService
from .models import DeviceEvent

logger = logging.getLogger(__name__)


EVENT_NOTIFICATION_COPY = {
    "offline": {
        "title": "Device Offline",
        "body": "{device} at {branch} is offline. Last seen: {detail}",
        "notification_type": "sync_issue",
    },
    "sync_failure": {
        "title": "Device Sync Issue",
        "body": "{device} at {branch} has not synced data. {detail}",
        "notification_type": "sync_issue",
    },
    "battery_low": {
        "title": "Battery Low",
        "body": "{device} at {branch} battery is low. {detail}",
        "notification_type": "alert",
    },
    "storage_full": {
        "title": "Storage Alert",
        "body": "{device} at {branch} is reporting high app storage use. {detail}",
        "notification_type": "alert",
    },
    "sim_change": {
        "title": "SIM Card Changed",
        "body": "{device} at {branch} reported SIM change. {detail}",
        "notification_type": "alert",
    },
    "network_weak": {
        "title": "Weak Network Signal",
        "body": "{device} at {branch} has weak signal. {detail}",
        "notification_type": "alert",
    },
    "permission_denied": {
        "title": "Permission Required",
        "body": "{device} at {branch} is missing required permissions. {detail}",
        "notification_type": "alert",
    },
    "app_crash": {
        "title": "App Crash Reported",
        "body": "{device} at {branch} reported an app crash. {detail}",
        "notification_type": "alert",
    },
    "app_uninstall_suspected": {
        "title": "Possible App Uninstall",
        "body": "{device} at {branch} may have removed or stopped the app. {detail}",
        "notification_type": "alert",
    },
}


class MonitoringAlertService:
    @staticmethod
    def _branch_name(device):
        return device.branch.spa_name if device and device.branch else "Unassigned branch"

    @staticmethod
    def _device_name(device):
        return device.phone_name or device.device_id or device.android_id or str(device.id)

    @staticmethod
    def _notification_data(event):
        device = event.device
        branch = device.branch if device else None
        return {
            "event_id": str(event.id),
            "event_type": event.event_type,
            "device_pk": str(device.id) if device else "",
            "device_id": device.device_id if device else "",
            "phone_name": device.phone_name if device else "",
            "branch_id": str(branch.id) if branch else "",
            "branch_name": branch.spa_name if branch else "",
            "source": "monitoring",
        }

    @staticmethod
    def _broadcast(event, action):
        try:
            device = event.device
            branch_id = str(device.branch_id) if device and device.branch_id else None
            groups = ["crm_dashboard"]
            if branch_id:
                groups.append(f"branch_{branch_id}")
                area_manager_ids = get_user_model().objects.filter(
                    role="area_manager",
                    area_branches__id=branch_id,
                    is_active=True,
                ).values_list("id", flat=True)
                groups.extend(f"area_manager_{manager_id}" for manager_id in area_manager_ids)

            payload = {
                "type": "broadcast_message",
                "message": {
                    "type": "monitoring_event",
                    "action": action,
                    "event": {
                        "id": str(event.id),
                        "event_type": event.event_type,
                        "description": event.description,
                        "resolved": event.resolved,
                        "device_uid": device.device_id if device else "N/A",
                        "branch_name": MonitoringAlertService._branch_name(device),
                        "created_at": event.created_at.isoformat() if event.created_at else None,
                        "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
                    },
                },
            }

            channel_layer = get_channel_layer()
            for group in set(groups):
                async_to_sync(channel_layer.group_send)(group, payload)
        except Exception:
            logger.exception("Failed to broadcast monitoring event", extra={"event_id": str(event.id)})

    @staticmethod
    def broadcast_device_status(device, status_type="heartbeat"):
        try:
            branch_id = str(device.branch_id) if device and device.branch_id else None
            groups = ["crm_dashboard"]
            if branch_id:
                groups.append(f"branch_{branch_id}")
                area_manager_ids = get_user_model().objects.filter(
                    role="area_manager",
                    area_branches__id=branch_id,
                    is_active=True,
                ).values_list("id", flat=True)
                groups.extend(f"area_manager_{manager_id}" for manager_id in area_manager_ids)

            payload = {
                "type": "broadcast_message",
                "message": {
                    "type": "monitoring_status",
                    "status_type": status_type,
                    "device": {
                        "id": str(device.id),
                        "device_id": device.device_id,
                        "phone_name": device.phone_name,
                        "branch_id": branch_id,
                        "branch_name": MonitoringAlertService._branch_name(device),
                        "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None,
                        "last_sync": device.last_sync.isoformat() if device.last_sync else None,
                        "is_online": device.is_online,
                    },
                },
            }
            channel_layer = get_channel_layer()
            for group in set(groups):
                async_to_sync(channel_layer.group_send)(group, payload)
        except Exception:
            logger.exception("Failed to broadcast monitoring device status", extra={"device_id": str(device.id)})

    @staticmethod
    def _notify_recipients(event):
        device = event.device
        copy = EVENT_NOTIFICATION_COPY.get(event.event_type)
        if not copy:
            return 0

        detail = event.description or event.get_event_type_display()
        body = copy["body"].format(
            device=MonitoringAlertService._device_name(device),
            branch=MonitoringAlertService._branch_name(device),
            detail=detail,
        )
        data = MonitoringAlertService._notification_data(event)
        recipients = []
        if device and device.is_active and not device.is_blocked:
            recipients.append(device)

        if device and device.branch_id:
            managers = get_user_model().objects.filter(
                is_active=True,
                fcm_token__isnull=False,
            ).filter(
                branch_id=device.branch_id,
                role="spa_manager",
            )
            recipients.extend(list(managers))

        sent_count = 0
        for recipient in recipients:
            if not getattr(recipient, "fcm_token", None):
                continue
            if NotificationService.send_push(
                recipient=recipient,
                title=copy["title"],
                body=body,
                notification_type=copy["notification_type"],
                data=data,
            ):
                sent_count += 1
        return sent_count

    @staticmethod
    def _merge_duplicate_events(events, description=None):
        canonical = events[0]
        duplicates = events[1:]
        if not duplicates:
            return canonical

        duplicate_ids = [str(event.id) for event in duplicates]
        descriptions = [event.description for event in events if event.description]
        selected_description = description or (descriptions[-1] if descriptions else canonical.description)
        latest_updated_at = max((event.updated_at for event in events if event.updated_at), default=canonical.updated_at)
        latest_created_at = max((event.created_at for event in events if event.created_at), default=canonical.created_at)

        update_fields = []
        if selected_description and canonical.description != selected_description:
            canonical.description = selected_description
            update_fields.append("description")
        if latest_updated_at and canonical.updated_at != latest_updated_at:
            canonical.updated_at = latest_updated_at
            update_fields.append("updated_at")

        if update_fields:
            DeviceEvent.objects.filter(pk=canonical.pk).update(
                **{field: getattr(canonical, field) for field in update_fields}
            )

        DeviceEvent.objects.filter(pk__in=[event.pk for event in duplicates]).delete()
        logger.warning(
            "Duplicate active DeviceEvent records merged",
            extra={
                "device_id": canonical.device.device_id if canonical.device else None,
                "event_type": canonical.event_type,
                "canonical_event_id": str(canonical.id),
                "duplicate_record_ids": duplicate_ids,
                "duplicate_count": len(duplicates),
                "earliest_created_at": canonical.created_at.isoformat() if canonical.created_at else None,
                "latest_occurrence_at": latest_created_at.isoformat() if latest_created_at else None,
            },
        )
        canonical.refresh_from_db()
        return canonical

    @staticmethod
    def _get_or_create_active_event(device, event_type, description):
        identity = {
            "device": device,
            "event_type": event_type,
            "resolved": False,
        }

        try:
            with transaction.atomic():
                events = list(
                    DeviceEvent.objects.select_for_update()
                    .filter(**identity)
                    .order_by("created_at", "id")
                )
                if events:
                    return MonitoringAlertService._merge_duplicate_events(events, description=description), False

                return DeviceEvent.objects.create(
                    device=device,
                    event_type=event_type,
                    resolved=False,
                    description=description,
                ), True
        except IntegrityError:
            with transaction.atomic():
                events = list(
                    DeviceEvent.objects.select_for_update()
                    .filter(**identity)
                    .order_by("created_at", "id")
                )
                if events:
                    return MonitoringAlertService._merge_duplicate_events(events, description=description), False
                raise

    @staticmethod
    def raise_event(device, event_type, description, notify=True, dedupe_active=True):
        if dedupe_active:
            event, created = MonitoringAlertService._get_or_create_active_event(device, event_type, description)
            if not created and event.description != description:
                event.description = description
                event.save(update_fields=["description", "updated_at"])
        else:
            event = DeviceEvent.objects.create(
                device=device,
                event_type=event_type,
                description=description,
            )
            created = True

        if created:
            if notify:
                MonitoringAlertService._notify_recipients(event)
            MonitoringAlertService._broadcast(event, "created")
        else:
            MonitoringAlertService._broadcast(event, "updated")
        return event

    @staticmethod
    def resolve_events(device, event_types):
        now = timezone.now()
        queryset = DeviceEvent.objects.filter(
            device=device,
            event_type__in=event_types,
            resolved=False,
        )
        events = list(queryset)
        queryset.update(resolved=True, resolved_at=now)
        for event in events:
            event.resolved = True
            event.resolved_at = now
            MonitoringAlertService._broadcast(event, "resolved")
        return len(events)


def offline_threshold():
    minutes = getattr(settings, "MONITORING_OFFLINE_AFTER_MINUTES", 20)
    return timezone.now() - timedelta(minutes=minutes)

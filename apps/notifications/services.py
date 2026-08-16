import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
from .models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def _recipient_context(recipient):
        return {
            "recipient_model": recipient.__class__.__name__,
            "recipient_id": str(getattr(recipient, "id", "")),
            "device_id": getattr(recipient, "device_id", None),
            "has_fcm_token": bool(getattr(recipient, "fcm_token", None)),
        }

    @staticmethod
    def _initialize_firebase():
        """Initialize Firebase Admin SDK if not already done."""
        if not firebase_admin._apps:
            # First try path from settings
            cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_KEY', None)
            if cred_path:
                try:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info(
                        "Firebase Admin SDK initialized from service account",
                        extra={
                            "firebase_project_id": getattr(cred, "project_id", None),
                            "credential_path": cred_path,
                        },
                    )
                except Exception as e:
                    logger.exception(
                        "Failed to initialize Firebase Admin SDK from service account",
                        extra={"credential_path": cred_path},
                    )
            else:
                # Fallback to default initialization (expects GOOGLE_APPLICATION_CREDENTIALS)
                try:
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin SDK initialized from application default credentials")
                except Exception:
                    logger.warning(
                        "Firebase not initialized. Push notifications will be logged but not sent.",
                        exc_info=True,
                    )

    @staticmethod
    def _broadcast_refresh(branch_id=None):
        """Broadcast a refresh signal to the dashboard group and specific branch group."""
        try:
            channel_layer = get_channel_layer()
            groups = NotificationService._groups_for_branch(branch_id)

            for group in dict.fromkeys(groups):
                async_to_sync(channel_layer.group_send)(
                    group,
                    {
                        "type": "broadcast_message",
                        "message": {
                            "type": "refresh_notifications"
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Failed to broadcast refresh: {e}")

    @staticmethod
    def _area_manager_groups_for_branch(branch_id):
        if not branch_id:
            return []
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            manager_ids = User.objects.filter(
                role="area_manager",
                is_active=True,
                area_branches__id=branch_id,
            ).values_list("id", flat=True)
            return [f"area_manager_{manager_id}" for manager_id in manager_ids]
        except Exception:
            logger.exception("Failed to resolve area manager notification groups")
            return []

    @staticmethod
    def _groups_for_branch(branch_id=None):
        groups = ["crm_dashboard"]
        if branch_id:
            groups.append(f"branch_{branch_id}")
            groups.extend(NotificationService._area_manager_groups_for_branch(branch_id))
        return list(dict.fromkeys(groups))

    @staticmethod
    def _broadcast_notification(notification_log):
        """Broadcast notification to the dashboard group for real-time updates."""
        try:
            channel_layer = get_channel_layer()
            branch_id = None
            if notification_log.device and notification_log.device.branch_id:
                branch_id = str(notification_log.device.branch_id)
            elif notification_log.user and notification_log.user.branch_id:
                branch_id = str(notification_log.user.branch_id)

            recipient_name = "N/A"
            if notification_log.device:
                recipient_name = notification_log.device.phone_name or notification_log.device.device_id
            elif notification_log.user:
                recipient_name = notification_log.user.full_name or notification_log.user.email
            
            groups = NotificationService._groups_for_branch(branch_id)

            payload = {
                "type": "broadcast_message",
                "message": {
                    "type": "notification_created",
                    "notification": {
                        "id": str(notification_log.id),
                        "title": notification_log.title,
                        "body": notification_log.body,
                        "notification_type": notification_log.notification_type,
                        "device_name": notification_log.device.device_id if notification_log.device else "N/A",
                        "recipient_name": recipient_name,
                        "recipient_type": "device" if notification_log.device_id else "user" if notification_log.user_id else "unknown",
                        "branch_name": notification_log.device.branch.spa_name if notification_log.device and notification_log.device.branch else notification_log.user.branch.spa_name if notification_log.user and notification_log.user.branch else "N/A",
                        "created_at": notification_log.created_at.isoformat(),
                        "is_sent": notification_log.is_sent
                    }
                }
            }

            for group in groups:
                async_to_sync(channel_layer.group_send)(group, payload)
                
        except Exception as e:
            logger.error(f"Failed to broadcast notification: {e}")

    @staticmethod
    def send_push(recipient=None, title=None, body=None, notification_type=None, data=None, device=None, user=None):
        """
        Sends a push notification to a Device or User using FCM.
        
        Args:
            recipient: The Device or User model instance.
            title: The notification title.
            body: The notification body text.
            notification_type: Internal category ('alert', 'reminder', 'system', 'sync_issue').
            data: Optional dictionary of extra key-value pairs for the data payload.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        recipient = recipient or device or user
        if recipient is None:
            logger.error("FCM send skipped: no recipient provided")
            return False

        # Determine if recipient is a Device or User (simplified check)
        from apps.devices.models import Device
        from django.contrib.auth import get_user_model
        User = get_user_model()

        is_device = isinstance(recipient, Device)
        is_user = isinstance(recipient, User)
        
        # Create the local log record (Note: existing Notification model requires Device)
        # For now, if it's a User, we might need to adjust or skip local logging if we don't have a device reference.
        # However, many times users have a "primary device". 
        # Requirement check: "store FCM device token for each manager"
        
        notif_log = None
        if is_device:
            notif_log = Notification.objects.create(
                device=recipient,
                title=title,
                body=body,
                notification_type=notification_type
            )
        elif is_user:
            notif_log = Notification.objects.create(
                user=recipient,
                title=title,
                body=body,
                notification_type=notification_type
            )

        NotificationService._initialize_firebase()

        token = recipient.fcm_token
        logger.info(
            "FCM send started",
            extra={
                **NotificationService._recipient_context(recipient),
                "notification_type": notification_type,
            },
        )
        if not token:
            if notif_log:
                notif_log.error_message = "Recipient has no FCM token saved."
                notif_log.save()
                NotificationService._broadcast_notification(notif_log)
            logger.warning(
                "FCM send skipped: recipient has no saved token",
                extra=NotificationService._recipient_context(recipient),
            )
            return False

        if not firebase_admin._apps:
            if notif_log:
                notif_log.error_message = "Firebase Admin SDK not initialized."
                notif_log.save()
                NotificationService._broadcast_notification(notif_log)
            logger.error(
                "FCM send skipped: Firebase Admin SDK not initialized",
                extra=NotificationService._recipient_context(recipient),
            )
            return False

        try:
            sent_at = timezone.now()
            message_data = {
                "title": str(title),
                "body": str(body),
                "type": str(notification_type),
                "sent_at": sent_at.isoformat(),
                "sent_at_ms": str(int(sent_at.timestamp() * 1000)),
                **{str(key): str(value) for key, value in (data or {}).items()},
            }
            if notif_log:
                message_data.setdefault("notification_id", str(notif_log.id))

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=message_data,
                token=token,
            )
            response = messaging.send(message)
            
            if notif_log:
                notif_log.is_sent = True
                notif_log.firebase_message_id = response
                notif_log.save()
                NotificationService._broadcast_notification(notif_log)
            logger.info(
                "FCM send succeeded",
                extra={
                    **NotificationService._recipient_context(recipient),
                    "firebase_message_id": response,
                },
            )
            return True
            
        except messaging.ApiCallError as e:
            logger.error(
                "FCM send failed with Firebase API error",
                extra={
                    **NotificationService._recipient_context(recipient),
                    "firebase_error_code": getattr(e, "code", None),
                    "firebase_error": str(e),
                },
            )
            if notif_log:
                notif_log.error_message = str(e)
                notif_log.save()
                NotificationService._broadcast_notification(notif_log)
            
            # Common FCM error codes/messages for stale or invalid tokens.
            error_code = str(getattr(e, "code", "") or "").lower()
            error_text = str(e).lower()
            invalid_token_codes = {
                "registration-token-not-registered",
                "invalid-registration-token",
                "unregistered",
                "invalid-argument",
            }
            invalid_token_error = (
                error_code in invalid_token_codes
                or "registration token is not registered" in error_text
                or "requested entity was not found" in error_text
                or "not a valid fcm registration token" in error_text
            )
            if invalid_token_error:
                logger.warning(
                    "Clearing invalid FCM token for recipient",
                    extra=NotificationService._recipient_context(recipient),
                )
                if is_device:
                    try:
                        from apps.monitoring.compliance import DeviceComplianceService
                        DeviceComplianceService.mark_fcm_invalid(recipient, str(e))
                    except Exception:
                        logger.exception("Failed to mark device FCM token invalid")
                recipient.fcm_token = None
                recipient.save(update_fields=['fcm_token'])
            
            return False

        except Exception as e:
            logger.exception(
                "Unexpected FCM send failure",
                extra=NotificationService._recipient_context(recipient),
            )
            if notif_log:
                notif_log.error_message = str(e)
                notif_log.save()
                NotificationService._broadcast_notification(notif_log)
            return False

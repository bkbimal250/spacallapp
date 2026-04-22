import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)

class NotificationService:
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
                except Exception as e:
                    logger.error(f"Failed to initialize Firebase with {cred_path}: {e}")
            else:
                # Fallback to default initialization (expects GOOGLE_APPLICATION_CREDENTIALS)
                try:
                    firebase_admin.initialize_app()
                except Exception:
                    logger.warning("Firebase not initialized. Push notifications will be logged but not sent.")

    @staticmethod
    def send_push(recipient, title, body, notification_type, data=None):
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
        # Determine if recipient is a Device or User (simplified check)
        from apps.devices.models import Device
        from django.contrib.auth import get_user_model
        User = get_user_model()

        is_device = isinstance(recipient, Device)
        
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

        token = recipient.fcm_token
        if not token:
            if notif_log:
                notif_log.error_message = "Recipient has no FCM token saved."
                notif_log.save()
            return False

        if not firebase_admin._apps:
            if notif_log:
                notif_log.error_message = "Firebase Admin SDK not initialized."
                notif_log.save()
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "type": notification_type,
                    **(data or {})
                },
                token=token,
            )
            response = messaging.send(message)
            
            if notif_log:
                notif_log.is_sent = True
                notif_log.firebase_message_id = response
                notif_log.save()
            return True
            
        except messaging.ApiCallError as e:
            logger.error(f"FCM ApiCallError for {recipient}: {e}")
            if notif_log:
                notif_log.error_message = str(e)
                notif_log.save()
            
            # Common FCM error codes for stale/invalid tokens
            invalid_token_codes = ['registration-token-not-registered', 'invalid-registration-token']
            if e.code in invalid_token_codes:
                logger.warning(f"Clearing invalid FCM token for {recipient}")
                recipient.fcm_token = None
                recipient.save(update_fields=['fcm_token'])
            
            return False

        except Exception as e:
            logger.error(f"Unexpected FCM Error for {recipient}: {e}")
            if notif_log:
                notif_log.error_message = str(e)
                notif_log.save()
            return False

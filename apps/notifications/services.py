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
    def send_push(device, title, body, notification_type, data=None):
        """
        Sends a push notification to an Android device using FCM.
        
        Args:
            device: The Device model instance.
            title: The notification title.
            body: The notification body text.
            notification_type: Internal category ('alert', 'reminder', 'system', 'sync_issue').
            data: Optional dictionary of extra key-value pairs for the data payload.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        # Create the local log record first
        notif_log = Notification.objects.create(
            device=device,
            title=title,
            body=body,
            notification_type=notification_type
        )

        if not device.fcm_token:
            notif_log.error_message = "Device has no FCM token saved."
            notif_log.save()
            return False

        if not firebase_admin._apps:
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
                token=device.fcm_token,
            )
            response = messaging.send(message)
            
            notif_log.is_sent = True
            notif_log.firebase_message_id = response
            notif_log.save()
            return True
            
        except Exception as e:
            logger.error(f"FCM Send Error for device {device.device_id}: {e}")
            notif_log.error_message = str(e)
            notif_log.save()
            return False

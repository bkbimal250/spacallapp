from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class RealTimeService:
    @staticmethod
    def broadcast_user_login(user):
        """
        Broadcast user login event to crm_dashboard group.
        """
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Realtime channel layer is not configured; skipping login broadcast.")
            return

        event_data = {
            "type": "user_login",
            "user_id": str(user.id),
            "name": user.full_name,
            "role": user.role,
            "branch": str(user.branch.spa_name) if user.branch else "N/A",
            "time": timezone.now().isoformat(),
        }
        
        try:
            async_to_sync(channel_layer.group_send)(
                "crm_dashboard",
                {
                    "type": "broadcast_message",
                    "message": event_data
                }
            )
        except Exception:
            logger.warning("Realtime login broadcast failed; continuing login.", exc_info=True)

    @staticmethod
    def broadcast_user_status(user, is_online):
        """
        Broadcast user status change event.
        """
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Realtime channel layer is not configured; skipping status broadcast.")
            return

        event_data = {
            "type": "user_status_change",
            "user_id": str(user.id),
            "is_online": is_online,
            "last_seen_at": timezone.now().isoformat(),
        }
        
        try:
            async_to_sync(channel_layer.group_send)(
                "crm_dashboard",
                {
                    "type": "broadcast_message",
                    "message": event_data
                }
            )
        except Exception:
            logger.warning("Realtime status broadcast failed; continuing request.", exc_info=True)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

class RealTimeService:
    @staticmethod
    def broadcast_user_login(user):
        """
        Broadcast user login event to crm_dashboard group.
        """
        channel_layer = get_channel_layer()
        event_data = {
            "type": "user_login",
            "user_id": str(user.id),
            "name": user.full_name,
            "role": user.role,
            "branch": str(user.branch.spa_name) if user.branch else "N/A",
            "time": timezone.now().isoformat(),
        }
        
        async_to_sync(channel_layer.group_send)(
            "crm_dashboard",
            {
                "type": "broadcast_message",
                "message": event_data
            }
        )

    @staticmethod
    def broadcast_user_status(user, is_online):
        """
        Broadcast user status change event.
        """
        channel_layer = get_channel_layer()
        event_data = {
            "type": "user_status_change",
            "user_id": str(user.id),
            "is_online": is_online,
            "last_seen_at": timezone.now().isoformat(),
        }
        
        async_to_sync(channel_layer.group_send)(
            "crm_dashboard",
            {
                "type": "broadcast_message",
                "message": event_data
            }
        )

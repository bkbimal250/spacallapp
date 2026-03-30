import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from channels.db import database_sync_to_async

class CRMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        print("USER:", self.user)  # 🔍 DEBUG

    # Safe check
        if not self.user or not self.user.is_authenticated:
            print("❌ Not authenticated")
            await self.close()
            return

    # Safe role check
        user_role = getattr(self.user, "role", None)

        if user_role not in ["admin", "super_admin", "branch_manager"]:
            print("❌ Invalid role:", user_role)
            await self.close()
            return

        self.group_name = "crm_dashboard"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print("✅ WebSocket connected")



    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Check if this was the last active session for this user
            # In a real-world scenario, you might want to track this in Redis
            # Here, we mark the user as offline on disconnect
            await self.update_user_status(False)
            
            # Leave the dashboard group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def broadcast_message(self, event):
        """
        Handle messages sent via group_send.
        """
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def update_user_status(self, is_online):
        """
        Update is_online status in the database.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # In a more advanced implementation, we would check for multiple connections
        # using Redis before setting is_online=False.
        User.objects.filter(id=self.user.id).update(
            is_online=is_online,
            last_seen_at=timezone.now()
        )

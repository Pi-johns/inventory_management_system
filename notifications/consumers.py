import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connect WebSocket based on user role."""
        if self.scope["user"] and not isinstance(self.scope["user"], AnonymousUser):
            self.user = self.scope["user"]

            if self.user.role in ['superadmin', 'manager']:
                self.room_group_name = 'notifications_admins'
            else:
                self.room_group_name = f'notifications_{self.user.id}'

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Disconnect WebSocket and remove user from the notification group."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_notification(self, event):
        """Send a notification message."""
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))

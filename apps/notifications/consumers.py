import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        
        if self.user and self.user.is_authenticated:
            self.room_group_name = f"user_{self.user.id}_notifications"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"User {self.user.id} joined notifications channel")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def notification_event(self, event):
        """
        Called when EventDispatcher pushes a notification to the group.
        """
        await self.send(text_data=json.dumps({
            'type': event.get('event', 'notification.created'),
            'payload': event.get('payload', {})
        }))

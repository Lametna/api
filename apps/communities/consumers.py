import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class CommunityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.community_id = self.scope['url_route']['kwargs']['community_id']
        
        if self.user and self.user.is_authenticated:
            self.room_group_name = f"community_{self.community_id}"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"User {self.user.id} joined community websocket {self.community_id}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def community_event(self, event):
        """
        Generic handler to send JSON down to WebSocket.
        Triggered by `EventDispatcher` or group broadcasts.
        """
        await self.send(text_data=json.dumps(event))

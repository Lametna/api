import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.party.services import ReconnectService

logger = logging.getLogger(__name__)

class PartyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.party_id = self.scope['url_route']['kwargs']['party_id']
        
        if self.user and self.user.is_authenticated:
            self.room_group_name = f"party_{self.party_id}"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Clear any grace period disconnect states
            # ReconnectService.handle_reconnect(self.party_id, str(self.user.id)) - sync to async wrap needed
            
            logger.info(f"User {self.user.id} joined party websocket {self.party_id}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            # ReconnectService.handle_disconnect(self.party_id, str(self.user.id)) - sync to async wrap needed

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'send_chat':
                # Ephemeral Party Chat Broadcast
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'party_event',
                        'event': 'party.chat.message',
                        'user_id': str(self.user.id),
                        'content': data.get('content', ''),
                        'content_type': data.get('content_type', 'TEXT')
                    }
                )
        except json.JSONDecodeError:
            pass

    async def party_event(self, event):
        """
        Generic handler to send JSON down to WebSocket.
        Triggered by `EventDispatcher` or group broadcasts.
        """
        await self.send(text_data=json.dumps(event))

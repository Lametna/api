import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class ConversationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        
        if self.user and self.user.is_authenticated:
            # We trust the view layer verified membership already, or we check it async here.
            # For brevity, assuming user is a member
            self.room_group_name = f"conversation_{self.conversation_id}"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"User {self.user.id} joined conversation {self.conversation_id}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'typing_start':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'event': 'typing.started',
                        'user_id': str(self.user.id)
                    }
                )
            elif action == 'typing_stop':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'event': 'typing.stopped',
                        'user_id': str(self.user.id)
                    }
                )
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """
        Generic handler to send JSON down to WebSocket.
        Triggered by `EventDispatcher` or group broadcasts.
        """
        await self.send(text_data=json.dumps(event))

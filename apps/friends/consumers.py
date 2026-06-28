import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        
        if self.user and self.user.is_authenticated:
            self.user_group_name = f"user_{self.user.id}"
            
            # Join personal notification group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Set presence to online
            await self.set_user_online()
            logger.info(f"WebSocket Connected: {self.user.id}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            await self.set_user_offline()
            logger.info(f"WebSocket Disconnected: {self.user.id}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages (e.g., heartbeats).
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'heartbeat':
                await self.set_user_online()
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_ack'
                }))
        except json.JSONDecodeError:
            pass

    # Broadcast Handlers
    async def friend_event(self, event):
        """
        Generic handler for friend.* events
        """
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'payload': event['payload']
        }))

    # Database operations
    @database_sync_to_async
    def set_user_online(self):
        from apps.friends.services import PresenceService
        PresenceService.set_online(self.user.id)

    @database_sync_to_async
    def set_user_offline(self):
        from apps.friends.services import PresenceService
        PresenceService.set_offline(self.user.id)

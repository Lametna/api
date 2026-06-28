import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        
        if self.user and self.user.is_authenticated:
            self.room_group_name = f"match_{self.match_id}"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"User {self.user.id} joined match websocket {self.match_id}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # We process live turn actions via WebSockets for high frequency games
        try:
            data = json.loads(text_data)
            action_type = data.get('type')
            
            if action_type == 'TURN_ACTION':
                # Pass the action to the plugin via a Celery task or sync wrapper
                pass
        except json.JSONDecodeError:
            pass

    async def game_event(self, event):
        """
        Broadcasts game engine state changes (ticks, new turns, score updates) 
        pushed by the EventDispatcher or Redis workers.
        """
        await self.send(text_data=json.dumps(event))

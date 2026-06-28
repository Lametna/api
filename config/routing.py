from django.urls import re_path
from apps.friends.consumers import PresenceConsumer
from apps.messaging.consumers import ConversationConsumer
from apps.notifications.consumers import NotificationConsumer
from apps.party.consumers import PartyConsumer
from apps.communities.consumers import CommunityConsumer
from apps.games.consumers import MatchConsumer

websocket_urlpatterns = [
    re_path(r'ws/presence/$', PresenceConsumer.as_asgi()),
    re_path(r'ws/conversations/(?P<conversation_id>[0-9a-f-]+)/$', ConversationConsumer.as_asgi()),
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/parties/(?P<party_id>[0-9a-f-]+)/$', PartyConsumer.as_asgi()),
    re_path(r'ws/communities/(?P<community_id>[0-9a-f-]+)/$', CommunityConsumer.as_asgi()),
    re_path(r'ws/matches/(?P<match_id>[0-9a-f-]+)/$', MatchConsumer.as_asgi()),
]

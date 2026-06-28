from django.contrib.auth import get_user_model
from apps.common.events import EventDispatcher, MatchFinishedEvent, MessageSentEvent, CommunityJoinedEvent
from .services import XPService, StatisticsService, AchievementService

User = get_user_model()

class ProgressionSubscriber:
    """
    Subscribes to universal Domain Events to drive progression.
    In a true production environment, these handlers would dispatch Celery tasks
    to avoid blocking the HTTP/WebSocket threads.
    """
    
    @staticmethod
    def setup():
        EventDispatcher.subscribe(MatchFinishedEvent, ProgressionSubscriber.handle_match_finished)
        EventDispatcher.subscribe(MessageSentEvent, ProgressionSubscriber.handle_message_sent)
        EventDispatcher.subscribe(CommunityJoinedEvent, ProgressionSubscriber.handle_community_joined)

    @staticmethod
    def handle_match_finished(event: MatchFinishedEvent):
        # We need the user objects. In a real system, the event might carry user_ids
        # Since this is a placeholder implementation, we just mock the concept.
        # users = MatchSelector.get_players(event.match_id)
        # for user in users:
        #    XPService.award_xp(user, 100, "MATCH_FINISHED")
        #    StatisticsService.increment(user, 'matches_played')
        pass

    @staticmethod
    def handle_message_sent(event: MessageSentEvent):
        # user = User.objects.get(id=event.sender_id)
        # StatisticsService.increment(user, 'messages_sent')
        # AchievementService.evaluate_achievement(user, 'social_butterfly', 1)
        pass

    @staticmethod
    def handle_community_joined(event: CommunityJoinedEvent):
        # user = User.objects.get(id=event.user_id)
        # StatisticsService.increment(user, 'community_count')
        # XPService.award_xp(user, 50, "COMMUNITY_JOINED")
        pass

# Initialize subscriptions when the app is loaded
# (This would ideally be called in apps.py ready() function)
ProgressionSubscriber.setup()

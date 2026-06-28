import logging
from django.contrib.auth import get_user_model
from apps.common.events import EventDispatcher, MatchFinishedEvent
from .services import RankingService, StatisticsService

logger = logging.getLogger(__name__)
User = get_user_model()

class CompetitiveSubscriber:
    """
    Subscribes to Game Match events.
    If a game marks a match as 'ranked', this updates the Elo rating without the
    Game Plugin needing to know what 'Elo' is.
    """
    
    @staticmethod
    def setup():
        EventDispatcher.subscribe(MatchFinishedEvent, CompetitiveSubscriber.handle_match_finished)

    @staticmethod
    def handle_match_finished(event: MatchFinishedEvent):
        try:
            # MVP: Assuming a 1v1 match structure to easily apply Elo.
            # In a real scenario, the MatchFinishedEvent should carry the specific user_ids and their scores.
            pass
            # Example logic if event had explicit winners/losers:
            # winner = User.objects.get(id=event.winner_id)
            # loser = User.objects.get(id=event.loser_id)
            # 
            # If event.is_ranked:
            #   RankingService.adjust_rating(winner, event.game_id, 1000, True)
            #   RankingService.adjust_rating(loser, event.game_id, 1000, False)
            #
            # StatisticsService.process_match_result(winner, True, event.is_tournament)
            # StatisticsService.process_match_result(loser, False, event.is_tournament)
            
        except Exception as e:
            logger.error(f"CompetitiveEngine failed to process match: {e}")

CompetitiveSubscriber.setup()

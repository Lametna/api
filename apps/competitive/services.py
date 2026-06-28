from typing import Tuple
from django.contrib.auth import get_user_model

from .repositories import RankingRepository, LeaderboardRepository, TournamentRepository, StatisticsRepository
from .selectors import RankingSelector, TournamentSelector
from apps.common.events import (
    EventDispatcher, PlayerPromotedEvent, PlayerDemotedEvent, TournamentStartedEvent
)

User = get_user_model()

class RankingService:
    @staticmethod
    def adjust_rating(user: User, game_id: str, opponent_rating: int, is_win: bool) -> None:
        """Standard Elo Implementation MVP"""
        current_rating_obj = RankingSelector.get_player_rating(user, game_id)
        current_rating = current_rating_obj.current_rating if current_rating_obj else 1000
        
        # Elo Expected Score Formula
        expected = 1 / (1 + 10 ** ((opponent_rating - current_rating) / 400))
        k_factor = 32
        actual = 1 if is_win else 0
        
        new_rating = int(current_rating + k_factor * (actual - expected))
        if new_rating < 0: new_rating = 0
        
        # Determine new tier
        new_tier = RankingSelector.get_rank_tier_for_rating(new_rating)
        
        _, tier_changed = RankingRepository.update_rating(user, game_id, new_rating, new_tier)
        
        if tier_changed and current_rating_obj and current_rating_obj.tier:
            if new_rating > current_rating:
                EventDispatcher.publish(PlayerPromotedEvent(player_id=str(user.id), new_tier=new_tier.name, game_id=game_id))
            else:
                EventDispatcher.publish(PlayerDemotedEvent(player_id=str(user.id), new_tier=new_tier.name, game_id=game_id))

class LeaderboardService:
    @staticmethod
    def add_score(user: User, leaderboard_id: str, score_delta: int) -> None:
        # In a real Redis-backed system: redis.zincrby(leaderboard_id, score_delta, user.id)
        # MVP Postgres fallback:
        # We need a get-and-increment here, simplified for now:
        LeaderboardRepository.update_score(user, leaderboard_id, score_delta)

class TournamentService:
    @staticmethod
    def register(user: User, tournament_id: str) -> Tuple[bool, str]:
        t = TournamentSelector.get_tournament(tournament_id)
        if not t or t.status != 'REGISTERING':
            return False, "Tournament not available for registration."
            
        participants = TournamentSelector.get_participants(tournament_id)
        if len(participants) >= t.max_participants:
            return False, "Tournament is full."
            
        TournamentRepository.register_participant(tournament_id, user)
        return True, "Registered successfully."

class BracketService:
    @staticmethod
    def generate_bracket(tournament_id: str) -> bool:
        t = TournamentSelector.get_tournament(tournament_id)
        if not t: return False
        
        participants = TournamentSelector.get_participants(tournament_id)
        # Very simplified generation: pair participants sequentially for Round 1
        num_participants = len(participants)
        
        TournamentRepository.update_status(tournament_id, 'RUNNING')
        
        for i in range(0, num_participants, 2):
            p1 = participants[i]
            p2 = participants[i+1] if i+1 < num_participants else None
            TournamentRepository.create_match_node(tournament_id, 1, p1, p2)
            
        EventDispatcher.publish(TournamentStartedEvent(tournament_id=tournament_id))
        return True

class StatisticsService:
    @staticmethod
    def process_match_result(user: User, is_win: bool, is_tournament: bool = False) -> None:
        StatisticsRepository.record_match(user, is_win, is_tournament)

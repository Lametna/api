from typing import Dict, Any, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    PlayerRating, RankTier, LeaderboardEntry, Tournament, TournamentParticipant, TournamentMatch,
    CompetitiveStatistics
)

User = get_user_model()

class RankingRepository:
    @staticmethod
    def update_rating(user: User, game_id: str, new_rating: int, new_tier: RankTier) -> Tuple[PlayerRating, bool]:
        rating, created = PlayerRating.objects.get_or_create(
            user=user, game_id=game_id, 
            defaults={'current_rating': new_rating, 'peak_rating': new_rating, 'tier': new_tier}
        )
        
        tier_changed = False
        if not created:
            if rating.tier != new_tier:
                tier_changed = True
            rating.current_rating = new_rating
            rating.tier = new_tier
            if new_rating > rating.peak_rating:
                rating.peak_rating = new_rating
            rating.save(update_fields=['current_rating', 'peak_rating', 'tier'])
            
        return rating, tier_changed

class LeaderboardRepository:
    @staticmethod
    def update_score(user: User, leaderboard_id: str, score: int) -> LeaderboardEntry:
        entry, _ = LeaderboardEntry.objects.update_or_create(
            user=user, leaderboard_id=leaderboard_id,
            defaults={'score': score}
        )
        return entry

class TournamentRepository:
    @staticmethod
    def create_tournament(name: str, game_id: str, start_time: str, max_p: int) -> Tournament:
        return Tournament.objects.create(name=name, game_id=game_id, start_time=start_time, max_participants=max_p)

    @staticmethod
    def register_participant(tournament_id: str, user: User) -> TournamentParticipant:
        return TournamentParticipant.objects.create(tournament_id=tournament_id, user=user)

    @staticmethod
    def update_status(tournament_id: str, status: str) -> None:
        Tournament.objects.filter(id=tournament_id).update(status=status)

    @staticmethod
    def create_match_node(tournament_id: str, round_num: int, p1: TournamentParticipant = None, p2: TournamentParticipant = None) -> TournamentMatch:
        return TournamentMatch.objects.create(
            tournament_id=tournament_id, round_number=round_num,
            participant1=p1, participant2=p2
        )

class StatisticsRepository:
    @staticmethod
    def record_match(user: User, is_win: bool, is_tournament: bool = False) -> None:
        stats, _ = CompetitiveStatistics.objects.get_or_create(user=user)
        if is_win:
            stats.season_wins += 1
            if is_tournament: stats.tournament_wins += 1
        else:
            stats.season_losses += 1
            
        if is_tournament: stats.tournament_matches += 1
        
        stats.save(update_fields=['season_wins', 'season_losses', 'tournament_wins', 'tournament_matches'])

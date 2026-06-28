from typing import List, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Season, RankTier, PlayerRating, Leaderboard, LeaderboardEntry, 
    LiveEvent, Tournament, TournamentParticipant, TournamentMatch, CompetitiveStatistics
)

User = get_user_model()

class SeasonSelector:
    @staticmethod
    def get_current_season() -> Optional[Season]:
        now = timezone.now()
        return Season.objects.filter(start_time__lte=now, end_time__gte=now, is_active=True).first()

    @staticmethod
    def get_seasons() -> List[Season]:
        return list(Season.objects.all().order_by('-start_time'))
        
    @staticmethod
    def get_season(season_id: str) -> Optional[Season]:
        return Season.objects.filter(id=season_id).first()

class RankingSelector:
    @staticmethod
    def get_player_rating(user: User, game_id: str) -> Optional[PlayerRating]:
        return PlayerRating.objects.filter(user=user, game_id=game_id).first()

    @staticmethod
    def get_rank_tier_for_rating(rating: int) -> Optional[RankTier]:
        return RankTier.objects.filter(min_rating__lte=rating, max_rating__gte=rating).first()

    @staticmethod
    def get_all_tiers() -> List[RankTier]:
        return list(RankTier.objects.all())

class LeaderboardSelector:
    @staticmethod
    def get_leaderboards() -> List[Leaderboard]:
        return list(Leaderboard.objects.all())

    @staticmethod
    def get_leaderboard(lb_id: str) -> Optional[Leaderboard]:
        return Leaderboard.objects.filter(id=lb_id).first()
        
    @staticmethod
    def get_top_entries(lb_id: str, limit: int = 100) -> List[LeaderboardEntry]:
        # MVP: DB query. Prod: Redis ZREVRANGE.
        return list(LeaderboardEntry.objects.filter(leaderboard_id=lb_id).select_related('user').order_by('-score')[:limit])

class EventSelector:
    @staticmethod
    def get_active_events() -> List[LiveEvent]:
        now = timezone.now()
        return list(LiveEvent.objects.filter(start_time__lte=now, end_time__gte=now))

class TournamentSelector:
    @staticmethod
    def get_tournaments() -> List[Tournament]:
        return list(Tournament.objects.all().order_by('-start_time'))
        
    @staticmethod
    def get_tournament(t_id: str) -> Optional[Tournament]:
        return Tournament.objects.filter(id=t_id).first()

    @staticmethod
    def get_participants(t_id: str) -> List[TournamentParticipant]:
        return list(TournamentParticipant.objects.filter(tournament_id=t_id).select_related('user'))

    @staticmethod
    def get_bracket(t_id: str) -> List[TournamentMatch]:
        return list(TournamentMatch.objects.filter(tournament_id=t_id).order_by('-round_number'))

class StatisticsSelector:
    @staticmethod
    def get_statistics(user: User) -> Optional[CompetitiveStatistics]:
        return CompetitiveStatistics.objects.filter(user=user).first()

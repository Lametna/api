from typing import List, Optional
from django.contrib.auth import get_user_model
from .models import (
    PlayerProgress, PlayerLevel, Achievement, PlayerAchievement, 
    Challenge, PlayerChallenge, PlayerStatistics, PlayerBadge, PlayerTitle
)

User = get_user_model()

class ProgressSelector:
    @staticmethod
    def get_progress(user: User) -> Optional[PlayerProgress]:
        return PlayerProgress.objects.filter(user=user).first()

class LevelSelector:
    @staticmethod
    def get_level(level_number: int) -> Optional[PlayerLevel]:
        return PlayerLevel.objects.filter(level_number=level_number).first()
        
    @staticmethod
    def get_all_levels() -> List[PlayerLevel]:
        return list(PlayerLevel.objects.all().order_by('level_number'))

class AchievementSelector:
    @staticmethod
    def get_achievements() -> List[Achievement]:
        return list(Achievement.objects.filter(is_hidden=False))
        
    @staticmethod
    def get_player_achievements(user: User) -> List[PlayerAchievement]:
        return list(PlayerAchievement.objects.filter(user=user).select_related('achievement'))

class ChallengeSelector:
    @staticmethod
    def get_active_challenges() -> List[Challenge]:
        return list(Challenge.objects.filter(is_active=True))
        
    @staticmethod
    def get_player_challenges(user: User) -> List[PlayerChallenge]:
        return list(PlayerChallenge.objects.filter(user=user).select_related('challenge'))

class StatisticsSelector:
    @staticmethod
    def get_statistics(user: User) -> Optional[PlayerStatistics]:
        return PlayerStatistics.objects.filter(user=user).first()

class BadgeTitleSelector:
    @staticmethod
    def get_badges(user: User) -> List[PlayerBadge]:
        return list(PlayerBadge.objects.filter(user=user))
        
    @staticmethod
    def get_titles(user: User) -> List[PlayerTitle]:
        return list(PlayerTitle.objects.filter(user=user))

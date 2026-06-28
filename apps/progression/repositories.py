from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    PlayerProgress, ExperienceTransaction, PlayerAchievement, 
    PlayerChallenge, PlayerStreak, PlayerStatistics, PlayerBadge, PlayerTitle
)

User = get_user_model()

class ProgressRepository:
    @staticmethod
    def get_or_create_progress(user: User) -> PlayerProgress:
        progress, _ = PlayerProgress.objects.get_or_create(user=user)
        return progress

    @staticmethod
    def add_xp(user: User, amount: int, reason: str, context: Dict[str, Any] = None) -> PlayerProgress:
        with transaction.atomic():
            progress = ProgressRepository.get_or_create_progress(user)
            progress.total_xp += amount
            progress.save(update_fields=['total_xp'])
            
            ExperienceTransaction.objects.create(
                user=user, amount=amount, reason=reason, context=context or {}
            )
            return progress

    @staticmethod
    def update_level(progress: PlayerProgress, new_level: int) -> PlayerProgress:
        progress.current_level = new_level
        progress.save(update_fields=['current_level'])
        return progress

class AchievementRepository:
    @staticmethod
    def update_progress(user: User, achievement_id: str, value_to_add: int) -> PlayerAchievement:
        pa, created = PlayerAchievement.objects.get_or_create(user=user, achievement_id=achievement_id)
        if not pa.is_completed:
            pa.progress_value += value_to_add
            pa.save(update_fields=['progress_value'])
        return pa

    @staticmethod
    def complete_achievement(player_achievement: PlayerAchievement) -> PlayerAchievement:
        player_achievement.is_completed = True
        player_achievement.completed_at = timezone.now()
        player_achievement.save(update_fields=['is_completed', 'completed_at'])
        return player_achievement

class ChallengeRepository:
    @staticmethod
    def update_progress(user: User, challenge_id: str, value_to_add: int) -> PlayerChallenge:
        pc, created = PlayerChallenge.objects.get_or_create(
            user=user, challenge_id=challenge_id, 
            defaults={'expires_at': timezone.now() + timezone.timedelta(days=1)}
        )
        if not pc.is_completed and pc.expires_at > timezone.now():
            pc.progress_value += value_to_add
            pc.save(update_fields=['progress_value'])
        return pc

class StreakRepository:
    @staticmethod
    def increment_streak(user: User, streak_type: str) -> PlayerStreak:
        streak, created = PlayerStreak.objects.get_or_create(user=user, streak_type=streak_type)
        streak.current_count += 1
        if streak.current_count > streak.highest_count:
            streak.highest_count = streak.current_count
        streak.save(update_fields=['current_count', 'highest_count', 'last_updated'])
        return streak

    @staticmethod
    def reset_streak(user: User, streak_type: str) -> PlayerStreak:
        streak, created = PlayerStreak.objects.get_or_create(user=user, streak_type=streak_type)
        streak.current_count = 0
        streak.save(update_fields=['current_count', 'last_updated'])
        return streak

class StatisticsRepository:
    @staticmethod
    def get_or_create_stats(user: User) -> PlayerStatistics:
        stats, _ = PlayerStatistics.objects.get_or_create(user=user)
        return stats

    @staticmethod
    def increment_stat(user: User, stat_field: str, value: int = 1) -> PlayerStatistics:
        stats = StatisticsRepository.get_or_create_stats(user)
        current_val = getattr(stats, stat_field, 0)
        setattr(stats, stat_field, current_val + value)
        stats.save(update_fields=[stat_field])
        return stats

from typing import Tuple, List, Dict, Any
from django.contrib.auth import get_user_model

from .repositories import ProgressRepository, AchievementRepository, ChallengeRepository, StreakRepository, StatisticsRepository
from .selectors import ProgressSelector, LevelSelector
from apps.common.events import (
    EventDispatcher, PlayerLeveledUpEvent, XPEarnedEvent, AchievementUnlockedEvent, 
    ChallengeCompletedEvent, RewardGrantedEvent, BadgeUnlockedEvent, TitleUnlockedEvent
)

User = get_user_model()

class XPService:
    @staticmethod
    def award_xp(user: User, amount: int, reason: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        if amount <= 0: return False, "Amount must be positive"
        
        progress = ProgressRepository.add_xp(user, amount, reason, context)
        EventDispatcher.publish(XPEarnedEvent(player_id=str(user.id), amount=amount, reason=reason))
        
        # Check for level up
        next_level_obj = LevelSelector.get_level(progress.current_level + 1)
        if next_level_obj and progress.total_xp >= next_level_obj.xp_required:
            ProgressRepository.update_level(progress, next_level_obj.level_number)
            RewardService.grant_rewards(user, next_level_obj.rewards)
            EventDispatcher.publish(PlayerLeveledUpEvent(
                player_id=str(user.id), new_level=next_level_obj.level_number, reward_ids=list(next_level_obj.rewards.keys())
            ))
            
        return True, "XP Awarded"

class RewardService:
    @staticmethod
    def grant_rewards(user: User, rewards: Dict[str, Any]) -> None:
        if 'coins' in rewards:
            # Grant coins (future shop integration)
            pass
        if 'badge_id' in rewards:
            # Grant Badge
            EventDispatcher.publish(BadgeUnlockedEvent(player_id=str(user.id), badge_id=rewards['badge_id']))
        if 'title_id' in rewards:
            # Grant Title
            EventDispatcher.publish(TitleUnlockedEvent(player_id=str(user.id), title_id=rewards['title_id']))

class AchievementService:
    @staticmethod
    def evaluate_achievement(user: User, achievement_id: str, value_added: int) -> None:
        pa = AchievementRepository.update_progress(user, achievement_id, value_added)
        if not pa.is_completed and pa.progress_value >= pa.achievement.target_value:
            AchievementRepository.complete_achievement(pa)
            if pa.achievement.xp_reward > 0:
                XPService.award_xp(user, pa.achievement.xp_reward, f"ACHIEVEMENT_{pa.achievement.code}")
            EventDispatcher.publish(AchievementUnlockedEvent(player_id=str(user.id), achievement_id=achievement_id))

class StreakService:
    @staticmethod
    def process_streak(user: User, streak_type: str, time_delta_hours: float) -> None:
        # Simplistic streak evaluator
        if time_delta_hours <= 48:
            StreakRepository.increment_streak(user, streak_type)
        else:
            StreakRepository.reset_streak(user, streak_type)
            StreakRepository.increment_streak(user, streak_type)

class StatisticsService:
    @staticmethod
    def increment(user: User, stat_field: str, value: int = 1) -> None:
        StatisticsRepository.increment_stat(user, stat_field, value)

from rest_framework import serializers
from .models import (
    PlayerProgress, Achievement, PlayerAchievement, Challenge, 
    PlayerChallenge, PlayerStatistics, PlayerBadge, PlayerTitle
)

class PlayerProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerProgress
        fields = ['total_xp', 'current_level']

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'code', 'name', 'description', 'achievement_type', 'target_value', 'xp_reward']

class PlayerAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = PlayerAchievement
        fields = ['achievement', 'progress_value', 'is_completed', 'completed_at', 'reward_claimed']

class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['id', 'code', 'name', 'description', 'challenge_type', 'target_value', 'xp_reward']

class PlayerChallengeSerializer(serializers.ModelSerializer):
    challenge = ChallengeSerializer(read_only=True)
    
    class Meta:
        model = PlayerChallenge
        fields = ['challenge', 'progress_value', 'is_completed', 'completed_at', 'reward_claimed', 'expires_at']

class PlayerStatisticsSerializer(serializers.ModelSerializer):
    win_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = PlayerStatistics
        fields = [
            'matches_played', 'wins', 'losses', 'win_rate', 'hours_played',
            'party_count', 'community_count', 'messages_sent', 'friends_added'
        ]

class PlayerBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerBadge
        fields = ['badge_code', 'is_equipped', 'unlocked_at']

class PlayerTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerTitle
        fields = ['title_code', 'is_equipped', 'unlocked_at']

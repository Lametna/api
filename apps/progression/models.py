from django.db import models
from django.conf import settings
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class PlayerProgress(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    total_xp = models.BigIntegerField(default=0)
    current_level = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.user} - Lvl {self.current_level} ({self.total_xp} XP)"

class PlayerLevel(BaseModel):
    level_number = models.IntegerField(unique=True)
    xp_required = models.BigIntegerField()
    # E.g. {"coins": 100, "badge_id": "veteran"}
    rewards = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['level_number']

class ExperienceTransaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_history')
    amount = models.IntegerField()
    reason = models.CharField(max_length=100) # e.g. MATCH_WON, DAILY_LOGIN
    context = models.JSONField(default=dict, blank=True) # e.g. {"match_id": "uuid"}
    created_at = models.DateTimeField(auto_now_add=True)

class Achievement(BaseModel):
    class Type(models.TextChoices):
        ONE_TIME = 'ONE_TIME', 'One Time'
        PROGRESSIVE = 'PROGRESSIVE', 'Progressive'

    code = models.CharField(max_length=50, unique=True) # e.g. FIRST_BLOOD
    name = models.CharField(max_length=100)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=Type.choices, default=Type.ONE_TIME)
    target_value = models.IntegerField(default=1)
    is_hidden = models.BooleanField(default=False)
    xp_reward = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class PlayerAchievement(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    progress_value = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    reward_claimed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'achievement')

class Challenge(BaseModel):
    class Type(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=Type.choices)
    target_value = models.IntegerField(default=1)
    xp_reward = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

class PlayerChallenge(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    progress_value = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    reward_claimed = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

class PlayerStreak(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streaks')
    streak_type = models.CharField(max_length=50) # e.g. DAILY_LOGIN, WIN_STREAK
    current_count = models.IntegerField(default=0)
    highest_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'streak_type')

class PlayerStatistics(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statistics')
    matches_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    hours_played = models.FloatField(default=0.0)
    party_count = models.IntegerField(default=0)
    community_count = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)
    friends_added = models.IntegerField(default=0)
    
    @property
    def win_rate(self) -> float:
        if self.matches_played == 0: return 0.0
        return round(self.wins / self.matches_played, 2)

class PlayerBadge(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_code = models.CharField(max_length=50)
    is_equipped = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(auto_now_add=True)

class PlayerTitle(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='titles')
    title_code = models.CharField(max_length=50)
    is_equipped = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(auto_now_add=True)

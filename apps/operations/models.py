from django.db import models
from core.models import BaseModel

class Rule(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=100) # e.g., 'MatchFinishedEvent'
    condition_payload = models.JSONField(default=dict) # e.g., {"day_of_week": "SATURDAY", "game_mode": "RANKED"}
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-priority']

class RuleAction(BaseModel):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50) # e.g., 'GRANT_XP_MULTIPLIER', 'EMIT_REWARD_EVENT'
    action_payload = models.JSONField(default=dict) # e.g., {"multiplier": 2.0, "reason": "WEEKEND_EVENT"}

class FeatureFlag(BaseModel):
    flag_key = models.CharField(max_length=100, unique=True) # e.g., 'RANKED_MODE_ENABLED'
    description = models.TextField(blank=True)
    is_global_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return self.flag_key

class FeatureSegment(BaseModel):
    class ConditionType(models.TextChoices):
        COUNTRY = 'COUNTRY', 'Country Code'
        USER_ID = 'USER_ID', 'Specific User ID'
        USER_GROUP = 'USER_GROUP', 'User Group/Role'
        PERCENTAGE = 'PERCENTAGE', 'Rollout Percentage'

    flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='segments')
    condition_type = models.CharField(max_length=20, choices=ConditionType.choices)
    condition_value = models.CharField(max_length=100) # e.g., 'EG', 'BETA_TESTER', '25'
    is_active = models.BooleanField(default=True)

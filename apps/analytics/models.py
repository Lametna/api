from django.db import models
from apps.common.models import BaseModel

class MatchMetric(BaseModel):
    match_id = models.UUIDField(unique=True)
    game_id = models.CharField(max_length=255)
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    players_at_start = models.IntegerField(default=0)
    players_at_finish = models.IntegerField(default=0)
    quit_rate = models.FloatField(default=0.0)
    
    average_score = models.FloatField(default=0.0)
    winning_team = models.CharField(max_length=100, blank=True)
    
    def calculate_quit_rate(self):
        if self.players_at_start > 0:
            quits = self.players_at_start - self.players_at_finish
            self.quit_rate = max(0, quits / self.players_at_start)
        else:
            self.quit_rate = 0.0

    def calculate_duration(self):
        if self.started_at and self.finished_at:
            self.duration_seconds = int((self.finished_at - self.started_at).total_seconds())

    def __str__(self):
        return f"Metrics for {self.game_id} Match {self.match_id}"

class GamePopularityMetric(BaseModel):
    game_id = models.CharField(max_length=255, unique=True)
    total_matches = models.IntegerField(default=0)
    total_players = models.IntegerField(default=0)
    
    # JSON field to aggregate config keys (e.g. {"language": {"en": 500, "ar": 200}})
    popular_configs = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Popularity for {self.game_id}"

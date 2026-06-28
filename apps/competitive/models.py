from django.db import models
from django.conf import settings
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class Season(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

class RankTier(BaseModel):
    name = models.CharField(max_length=50) # e.g., Bronze, Silver, Diamond
    min_rating = models.IntegerField()
    max_rating = models.IntegerField()
    icon_url = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['min_rating']

class PlayerRating(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    game_id = models.CharField(max_length=100) # The game plugin ID
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True)
    current_rating = models.IntegerField(default=1000)
    peak_rating = models.IntegerField(default=1000)
    tier = models.ForeignKey(RankTier, on_delete=models.SET_NULL, null=True)

class Leaderboard(BaseModel):
    class Type(models.TextChoices):
        GLOBAL = 'GLOBAL', 'Global'
        COMMUNITY = 'COMMUNITY', 'Community'
        SEASON = 'SEASON', 'Season'
        
    name = models.CharField(max_length=100)
    leaderboard_type = models.CharField(max_length=20, choices=Type.choices)
    game_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

class LeaderboardEntry(BaseModel):
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.BigIntegerField(default=0)
    rank_position = models.IntegerField(null=True, blank=True) # Usually driven by Redis, but stored here for archival

class LiveEvent(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    modifiers = models.JSONField(default=dict) # e.g., {"xp_multiplier": 2.0}

class Tournament(BaseModel):
    class Status(models.TextChoices):
        REGISTERING = 'REGISTERING', 'Registering'
        RUNNING = 'RUNNING', 'Running'
        FINISHED = 'FINISHED', 'Finished'
        CANCELLED = 'CANCELLED', 'Cancelled'

    name = models.CharField(max_length=100)
    game_id = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    max_participants = models.IntegerField(default=16)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERING)
    rewards = models.JSONField(default=dict, blank=True)

class TournamentParticipant(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('tournament', 'user')

class TournamentMatch(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round_number = models.IntegerField()
    # A single-elimination tree node
    parent_match = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_matches')
    participant1 = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, related_name='matches_as_p1')
    participant2 = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, related_name='matches_as_p2')
    winner = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True, related_name='tournament_wins')
    match_ref_id = models.CharField(max_length=100, blank=True) # Links to actual Game Match ID

class CompetitiveStatistics(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='competitive_stats')
    season_wins = models.IntegerField(default=0)
    season_losses = models.IntegerField(default=0)
    tournament_wins = models.IntegerField(default=0)
    tournament_matches = models.IntegerField(default=0)

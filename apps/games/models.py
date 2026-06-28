from django.db import models
from django.conf import settings
from core.models import BaseModel
from apps.party.models import Party

User = settings.AUTH_USER_MODEL

class Game(BaseModel):
    plugin_id = models.CharField(max_length=100, unique=True) # e.g., 'lametna.games.trivia'
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default='1.0.0')
    developer = models.CharField(max_length=100, default='Lametna')
    
    min_players = models.IntegerField(default=1)
    max_players = models.IntegerField(default=64)
    estimated_duration_mins = models.IntegerField(default=10)
    difficulty = models.CharField(max_length=20, default='casual')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.plugin_id})"

class Match(BaseModel):
    class State(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        WAITING = 'WAITING', 'Waiting for Players'
        READY = 'READY', 'Ready'
        LOADING = 'LOADING', 'Loading'
        RUNNING = 'RUNNING', 'Running'
        PAUSED = 'PAUSED', 'Paused'
        FINISHED = 'FINISHED', 'Finished'
        CANCELLED = 'CANCELLED', 'Cancelled'
        ARCHIVED = 'ARCHIVED', 'Archived'

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='matches')
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    state = models.CharField(max_length=20, choices=State.choices, default=State.CREATED)
    
    configuration = models.JSONField(default=dict, blank=True) # E.g., {'rounds': 3, 'time_limit': 60}
    
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Match {self.id} - {self.state}"

class MatchPlayer(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ELIMINATED = 'ELIMINATED', 'Eliminated'
        DISCONNECTED = 'DISCONNECTED', 'Disconnected'
        SPECTATING = 'SPECTATING', 'Spectating'

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    team_id = models.CharField(max_length=50, blank=True, null=True) # For team-based games
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('match', 'user')

class Round(BaseModel):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.IntegerField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('match', 'round_number')

class Turn(BaseModel):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='turns')
    player = models.ForeignKey(MatchPlayer, on_delete=models.CASCADE)
    turn_number = models.IntegerField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class Score(BaseModel):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='scores')
    player = models.ForeignKey(MatchPlayer, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)
    reason = models.CharField(max_length=100, blank=True)
    
class GameResult(BaseModel):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='result')
    winners = models.ManyToManyField(MatchPlayer, related_name='won_matches')
    summary = models.JSONField(default=dict, blank=True)

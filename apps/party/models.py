from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class Party(BaseModel):
    class Privacy(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        PRIVATE = 'PRIVATE', 'Private'
        INVITE_ONLY = 'INVITE_ONLY', 'Invite Only'
        PASSWORD = 'PASSWORD', 'Password Protected'
        FRIENDS = 'FRIENDS', 'Friends Only'

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    privacy = models.CharField(max_length=20, choices=Privacy.choices, default=Privacy.INVITE_ONLY)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    max_players = models.IntegerField(default=4)
    language = models.CharField(max_length=10, default='en')
    
    is_active = models.BooleanField(default=True)
    current_game_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Party: {self.name} ({self.id})"

class PartyMember(BaseModel):
    class Role(models.TextChoices):
        HOST = 'HOST', 'Host'
        CO_HOST = 'CO_HOST', 'Co-Host'
        MEMBER = 'MEMBER', 'Member'

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='party_memberships')
    
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    current_screen = models.CharField(max_length=100, default='LOBBY')
    
    class Meta:
        unique_together = ('party', 'user')

class PartyInvitation(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELED = 'CANCELED', 'Canceled'

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='invitations')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_party_invites')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_party_invites')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()

    class Meta:
        # One pending invite per user per party
        constraints = [
            models.UniqueConstraint(
                fields=['party', 'receiver'],
                condition=models.Q(status='PENDING'),
                name='unique_pending_party_invite'
            )
        ]

class PartyGameQueue(BaseModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='game_queue')
    game_id = models.CharField(max_length=100) # Placeholder ID for future games module
    order = models.IntegerField(default=0)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['order', 'created_at']

class PartySession(BaseModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class Friendship(BaseModel):
    """
    Represents an accepted friendship between two users.
    Enforces user1.id < user2.id to prevent duplicate relational rows.
    """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_received')
    
    established_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-established_at']

    def clean(self):
        if self.user1_id == self.user2_id:
            raise ValidationError("Users cannot be friends with themselves.")
        if str(self.user1_id) > str(self.user2_id):
            # Enforce lexicographical ordering
            self.user1, self.user2 = self.user2, self.user1

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Friendship: {self.user1_id} <-> {self.user2_id}"

class FriendRequest(BaseModel):
    """
    State machine for pending friendship requests.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        DECLINED = 'DECLINED', _('Declined')
        CANCELED = 'CANCELED', _('Canceled')

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def clean(self):
        if self.sender_id == self.receiver_id:
            raise ValidationError("Cannot send a friend request to yourself.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Request from {self.sender_id} to {self.receiver_id} ({self.status})"

class BlockedUser(BaseModel):
    """
    Unidirectional block relationship.
    """
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')

    class Meta:
        unique_together = ('blocker', 'blocked')
        ordering = ['-created_at']

    def clean(self):
        if self.blocker_id == self.blocked_id:
            raise ValidationError("Users cannot block themselves.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Presence(models.Model):
    """
    Long-term persistent presence state.
    Volatile state (Online/Heartbeats) is stored in Redis.
    """
    class Status(models.TextChoices):
        ONLINE = 'ONLINE', _('Online')
        OFFLINE = 'OFFLINE', _('Offline')
        AWAY = 'AWAY', _('Away')
        BUSY = 'BUSY', _('Busy')
        INVISIBLE = 'INVISIBLE', _('Invisible')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence', primary_key=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)
    custom_message = models.CharField(max_length=100, blank=True)
    
    # Rich Presence Data
    current_activity = models.CharField(max_length=100, blank=True)
    current_game_id = models.CharField(max_length=100, blank=True)
    
    last_seen = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} - {self.status}"

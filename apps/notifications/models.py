from django.db import models
from django.conf import settings
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class Notification(BaseModel):
    class Type(models.TextChoices):
        FRIEND_REQUEST = 'FRIEND_REQUEST', 'Friend Request'
        FRIEND_ACCEPTED = 'FRIEND_ACCEPTED', 'Friend Accepted'
        MESSAGE = 'MESSAGE', 'Message'
        MENTION = 'MENTION', 'Mention'
        PARTY_INVITE = 'PARTY_INVITE', 'Party Invite'
        GAME_INVITE = 'GAME_INVITE', 'Game Invite'
        ACHIEVEMENT = 'ACHIEVEMENT', 'Achievement'
        SYSTEM = 'SYSTEM', 'System'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    type = models.CharField(max_length=30, choices=Type.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    
    title = models.CharField(max_length=100)
    body = models.TextField()
    action_url = models.CharField(max_length=255, blank=True)
    
    is_read = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

class NotificationPreference(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    email_mentions = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=False)
    
    in_app_mentions = models.BooleanField(default=True)
    in_app_messages = models.BooleanField(default=True)
    in_app_friend_requests = models.BooleanField(default=True)
    in_app_party_invites = models.BooleanField(default=True)
    
    sound_enabled = models.BooleanField(default=True)

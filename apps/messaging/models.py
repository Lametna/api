from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel
import uuid

User = settings.AUTH_USER_MODEL

class Conversation(BaseModel):
    is_group = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True, null=True) # For group chats
    last_activity = models.DateTimeField(auto_now_add=True)
    community = models.ForeignKey('communities.Community', on_delete=models.CASCADE, null=True, blank=True, related_name='channels')

    def __str__(self):
        return f"Conversation {self.id} (Group: {self.is_group})"

class ConversationMember(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    
    unread_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('conversation', 'user')

class Message(BaseModel):
    class ContentType(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        EMOJI = 'EMOJI', 'Emoji'
        SYSTEM = 'SYSTEM', 'System Message'
        IMAGE = 'IMAGE', 'Image Placeholder'
        FILE = 'FILE', 'File Placeholder'
        VOICE = 'VOICE', 'Voice Placeholder'
        GIF = 'GIF', 'GIF Placeholder'
        GAME_INVITE = 'GAME_INVITE', 'Game Invite Placeholder'
        PARTY_INVITE = 'PARTY_INVITE', 'Party Invite Placeholder'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    
    content_type = models.CharField(max_length=20, choices=ContentType.choices, default=ContentType.TEXT)
    content = models.TextField() # Text or URL depending on type
    
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False) # Soft delete
    
    class Meta:
        ordering = ['created_at']

class MessageReceipt(BaseModel):
    class Status(models.TextChoices):
        SENT = 'SENT', 'Sent'
        DELIVERED = 'DELIVERED', 'Delivered'
        READ = 'READ', 'Read'

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_receipts')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('message', 'user')

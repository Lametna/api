from django.db import models
from django.conf import settings
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class Community(BaseModel):
    class Privacy(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        PRIVATE = 'PRIVATE', 'Private'
        INVITE_ONLY = 'INVITE_ONLY', 'Invite Only'
        PASSWORD = 'PASSWORD', 'Password Protected'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    privacy = models.CharField(max_length=20, choices=Privacy.choices, default=Privacy.PUBLIC)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    
    max_members = models.IntegerField(default=1000)
    language = models.CharField(max_length=10, default='en')
    avatar = models.URLField(blank=True, null=True)
    banner = models.URLField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class CommunityMember(BaseModel):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Administrator'
        MODERATOR = 'MODERATOR', 'Moderator'
        MEMBER = 'MEMBER', 'Member'

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('community', 'user')

class CommunityInvitation(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        CANCELED = 'CANCELED', 'Canceled'

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='invitations')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_community_invites')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_community_invites')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

class CommunityPost(BaseModel):
    class Type(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
        IMAGE = 'IMAGE', 'Image Placeholder'
        POLL = 'POLL', 'Poll Placeholder'
        EVENT = 'EVENT', 'Event Post'

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.TEXT)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

class CommunityComment(BaseModel):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_deleted = models.BooleanField(default=False)

class CommunityReaction(BaseModel):
    class Type(models.TextChoices):
        LIKE = 'LIKE', 'Like'
        LOVE = 'LOVE', 'Love'
        LAUGH = 'LAUGH', 'Laugh'
        WOW = 'WOW', 'Wow'

    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True)
    comment = models.ForeignKey(CommunityComment, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=Type.choices)

    class Meta:
        # User can only react once per type per target
        unique_together = (('post', 'user', 'reaction_type'), ('comment', 'user', 'reaction_type'))

class CommunityEvent(BaseModel):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='events')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Future Game Platform Bindings
    game_id = models.CharField(max_length=100, blank=True, null=True)
    party = models.ForeignKey('party.Party', on_delete=models.SET_NULL, null=True, blank=True, related_name='community_events')
    
class CommunityBan(BaseModel):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='bans')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_bans')
    reason = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('community', 'user')

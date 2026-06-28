from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from core.models import SoftDeleteManager

class UserManager(BaseUserManager, SoftDeleteManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model for Lametna Platform.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(_('username'), max_length=150, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    display_name = models.CharField(_('display name'), max_length=100, blank=True)
    
    avatar = models.URLField(_('avatar url'), blank=True)
    
    # Preferences
    language = models.CharField(_('language'), max_length=10, default='en')
    theme = models.CharField(_('theme'), max_length=20, default='dark')
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    country = models.CharField(_('country'), max_length=2, blank=True)

    # Status
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps & Soft Delete (Manual implementation since we don't inherit BaseModel here to avoid ID collision)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} <{self.email}>"

def avatar_upload_path(instance, filename):
    return f"avatars/{instance.user.id}/{filename}"

def banner_upload_path(instance, filename):
    return f"banners/{instance.user.id}/{filename}"

class Profile(models.Model):
    """
    Extended user profile data.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', primary_key=True)
    biography = models.TextField(_('biography'), blank=True, max_length=500)
    birth_month = models.IntegerField(_('birth month'), null=True, blank=True)
    
    # Media (We store as URLField to abstract local vs remote storage, managed by our Storage service)
    avatar_url = models.URLField(_('avatar url'), blank=True)
    banner_url = models.URLField(_('banner url'), blank=True)
    
    # Cosmetics
    accent_color = models.CharField(_('accent color'), max_length=7, blank=True, default="#1D4ED8")
    
    # Links
    website = models.URLField(_('website'), blank=True)
    social_links = models.JSONField(_('social links'), default=dict, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class UserPreference(models.Model):
    """
    User settings and preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences', primary_key=True)
    
    # Accessibility
    reduced_motion = models.BooleanField(default=False)
    high_contrast = models.BooleanField(default=False)
    large_text = models.BooleanField(default=False)
    
    # General
    language = models.CharField(max_length=10, default='en')
    theme = models.CharField(max_length=20, default='dark')
    sidebar_state = models.CharField(max_length=20, default='expanded')
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

class UserPrivacy(models.Model):
    """
    Privacy and visibility settings.
    """
    class Visibility(models.TextChoices):
        PUBLIC = 'PUBLIC', _('Public')
        FRIENDS_ONLY = 'FRIENDS_ONLY', _('Friends Only')
        PRIVATE = 'PRIVATE', _('Private')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy', primary_key=True)
    
    profile_visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC)
    
    hide_email = models.BooleanField(default=True)
    hide_country = models.BooleanField(default=False)
    hide_activity = models.BooleanField(default=False)
    hide_statistics = models.BooleanField(default=False)
    hide_favorite_games = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

class FavoriteGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_games')
    game_id = models.CharField(max_length=100) # Placeholder for real game ID
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'game_id')
        ordering = ['-added_at']

class FavoriteCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_categories')
    category_name = models.CharField(max_length=100)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'category_name')

from django.contrib.auth import get_user_model
from typing import List
from .models import Notification, NotificationPreference

User = get_user_model()

class NotificationSelector:
    @staticmethod
    def get_user_notifications(user: User, limit=50) -> List[Notification]:
        return Notification.objects.filter(recipient=user).select_related('sender')[:limit]

    @staticmethod
    def get_unread_count(user: User) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).count()

class NotificationPreferenceSelector:
    @staticmethod
    def get_preferences(user: User) -> NotificationPreference:
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        return pref

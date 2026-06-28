from django.contrib.auth import get_user_model
from typing import List, Optional
from .models import Notification, NotificationPreference

User = get_user_model()

class NotificationRepository:
    @staticmethod
    def create_notification(recipient: User, n_type: str, title: str, body: str, sender: Optional[User] = None, action_url: str = "") -> Notification:
        return Notification.objects.create(
            recipient=recipient, sender=sender, type=n_type,
            title=title, body=body, action_url=action_url
        )

    @staticmethod
    def mark_read(notification: Notification) -> None:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    @staticmethod
    def mark_all_read(user: User) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

class NotificationPreferenceRepository:
    @staticmethod
    def update_preferences(user: User, **kwargs) -> NotificationPreference:
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        for k, v in kwargs.items():
            setattr(pref, k, v)
        pref.save()
        return pref

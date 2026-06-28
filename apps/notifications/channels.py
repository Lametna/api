from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
import logging

from .models import Notification
from .repositories import NotificationRepository
from apps.common.events import EventDispatcher, NotificationCreatedEvent
from .selectors import NotificationPreferenceSelector

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationChannel(ABC):
    """
    Abstract interface for delivering notifications.
    Implementations handle the specific delivery mechanism (In-App, Email, Push, etc.)
    """
    @abstractmethod
    def deliver(self, recipient: User, n_type: str, title: str, body: str, sender: Optional[User] = None, action_url: str = "") -> bool:
        pass


class InAppNotificationChannel(NotificationChannel):
    def deliver(self, recipient: User, n_type: str, title: str, body: str, sender: Optional[User] = None, action_url: str = "") -> bool:
        prefs = NotificationPreferenceSelector.get_preferences(recipient)
        
        # Preference Evaluation
        if n_type == Notification.Type.MESSAGE and not prefs.in_app_messages:
            return False
        if n_type == Notification.Type.FRIEND_REQUEST and not prefs.in_app_friend_requests:
            return False
        if n_type == Notification.Type.PARTY_INVITE and not prefs.in_app_party_invites:
            return False

        # Persist to Database
        notification = NotificationRepository.create_notification(recipient, n_type, title, body, sender, action_url)
        
        # Broadcast over WebSockets via Event Dispatcher
        EventDispatcher.publish(
            NotificationCreatedEvent(
                notification_id=str(notification.id),
                recipient_id=str(recipient.id),
                type=n_type,
                title=title
            )
        )
        return True


class EmailNotificationChannel(NotificationChannel):
    def deliver(self, recipient: User, n_type: str, title: str, body: str, sender: Optional[User] = None, action_url: str = "") -> bool:
        prefs = NotificationPreferenceSelector.get_preferences(recipient)
        
        # Preference Evaluation
        if n_type == Notification.Type.MESSAGE and not prefs.email_messages:
            return False
        if n_type == Notification.Type.MENTION and not prefs.email_mentions:
            return False
            
        # Stub: Actually send email here (e.g., using Celery to send via SES/SendGrid)
        logger.info(f"EMAIL DISPATCHED: To: {recipient.email} | Subject: {title}")
        return True


class NotificationDispatcher:
    """
    Fans out a notification payload to all registered channels.
    """
    channels = [
        InAppNotificationChannel(),
        EmailNotificationChannel()
    ]

    @classmethod
    def dispatch(cls, recipient: User, n_type: str, title: str, body: str, sender: Optional[User] = None, action_url: str = ""):
        for channel in cls.channels:
            try:
                channel.deliver(recipient, n_type, title, body, sender, action_url)
            except Exception as e:
                logger.error(f"Failed to deliver notification via {channel.__class__.__name__}: {str(e)}")

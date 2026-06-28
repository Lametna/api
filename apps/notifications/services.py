import logging
from typing import Optional
from django.contrib.auth import get_user_model

from .models import Notification
from .repositories import NotificationRepository, NotificationPreferenceRepository
from .channels import NotificationDispatcher
from apps.common.events import EventDispatcher, MessageSentEvent, NotificationReadEvent, FriendAcceptedEvent

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationService:
    @staticmethod
    def mark_as_read(user: User, notification_id: str) -> bool:
        notification = Notification.objects.filter(id=notification_id, recipient=user).first()
        if not notification:
            return False
            
        NotificationRepository.mark_read(notification)
        EventDispatcher.publish(NotificationReadEvent(notification_id=notification_id, user_id=str(user.id)))
        return True

    @staticmethod
    def mark_all_as_read(user: User) -> int:
        return NotificationRepository.mark_all_read(user)

    @staticmethod
    def delete_notification(user: User, notification_id: str) -> bool:
        deleted, _ = Notification.objects.filter(id=notification_id, recipient=user).delete()
        return deleted > 0

class NotificationPreferenceService:
    @staticmethod
    def update_preferences(user: User, **kwargs):
        return NotificationPreferenceRepository.update_preferences(user, **kwargs)

# --- Event Listener Bindings ---

def handle_message_sent(event: MessageSentEvent):
    from apps.messaging.models import Conversation
    from apps.messaging.selectors import ConversationSelector
    
    sender = User.objects.filter(id=event.sender_id).first()
    conv = Conversation.objects.filter(id=event.conversation_id).first()
    if not sender or not conv:
        return
        
    members = ConversationSelector.get_members(conv)
    for member in members:
        if member.id != sender.id:
            # Dispatch to channels
            NotificationDispatcher.dispatch(
                recipient=member,
                sender=sender,
                n_type=Notification.Type.MESSAGE,
                title=f"New message from {sender.display_name}",
                body=event.content[:50] + ("..." if len(event.content) > 50 else ""),
                action_url=f"/messages/{conv.id}"
            )

def handle_friend_accepted(event: FriendAcceptedEvent):
    user_a = User.objects.filter(id=event.user_a_id).first()
    user_b = User.objects.filter(id=event.user_b_id).first()
    
    if user_a and user_b:
        NotificationDispatcher.dispatch(
            recipient=user_a,
            sender=user_b,
            n_type=Notification.Type.FRIEND_ACCEPTED,
            title="Friend Request Accepted",
            body=f"{user_b.display_name} accepted your friend request."
        )
        NotificationDispatcher.dispatch(
            recipient=user_b,
            sender=user_a,
            n_type=Notification.Type.FRIEND_ACCEPTED,
            title="Friend Request Accepted",
            body=f"You and {user_a.display_name} are now friends."
        )

# Subscribe to Strongly Typed Events
EventDispatcher.subscribe(MessageSentEvent, handle_message_sent)
EventDispatcher.subscribe(FriendAcceptedEvent, handle_friend_accepted)

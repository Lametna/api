import logging
from typing import Tuple, Dict, Any, List
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .models import Conversation, Message
from .repositories import ConversationRepository, MessageRepository, ReceiptRepository
from .selectors import ConversationSelector, MessageSelector
from apps.common.events import (
    EventDispatcher, 
    MessageSentEvent, MessageEditedEvent, MessageDeletedEvent, MessageReadEvent, 
    ConversationCreatedEvent, TypingStartedEvent, TypingStoppedEvent
)

logger = logging.getLogger(__name__)
User = get_user_model()

class ConversationService:
    @staticmethod
    def get_or_create_direct_conversation(user1: User, user2: User) -> Tuple[bool, Any, str]:
        if user1.id == user2.id:
            return False, None, "Cannot create a conversation with yourself."
            
        if BlockSelector.is_blocked(user1, user2):
            return False, None, "Cannot create conversation with a blocked user."

        conv = ConversationSelector.get_direct_conversation(user1, user2)
        if conv:
            return True, conv, "Existing conversation retrieved."

        conv = ConversationRepository.create_direct_conversation(user1, user2)
        EventDispatcher.publish(ConversationCreatedEvent(
            conversation_id=str(conv.id), 
            members=[str(user1.id), str(user2.id)]
        ))
        return True, conv, "Conversation created."

class MessageService:
    @staticmethod
    def send_message(sender: User, conversation_id: str, content: str, content_type: str = 'TEXT') -> Tuple[bool, Any, str]:
        conv = Conversation.objects.filter(id=conversation_id).first()
        if not conv:
            return False, None, "Conversation not found."
            
        members = ConversationSelector.get_members(conv)
        if sender not in members:
            return False, None, "You are not a member of this conversation."
            
        if not conv.is_group:
            other_user = next((m for m in members if m.id != sender.id), None)
            if other_user and BlockSelector.is_blocked(sender, other_user):
                return False, None, "Cannot send message. You are blocked or have blocked this user."

        msg = MessageRepository.create_message(conv, sender, content, content_type)
        
        EventDispatcher.publish(MessageSentEvent(
            sender_id=str(sender.id),
            conversation_id=str(conv.id),
            content=content,
            content_type=content_type
        ))
        
        return True, msg, "Message sent."

    @staticmethod
    def edit_message(user: User, message_id: str, new_content: str) -> Tuple[bool, str]:
        msg = Message.objects.filter(id=message_id).first()
        if not msg:
            return False, "Message not found."
        if msg.sender_id != user.id:
            return False, "You can only edit your own messages."
        if msg.is_deleted:
            return False, "Cannot edit a deleted message."

        MessageRepository.edit_message(msg, new_content)
        EventDispatcher.publish(MessageEditedEvent(
            message_id=str(msg.id),
            content=new_content
        ))
        return True, "Message edited."

    @staticmethod
    def delete_message(user: User, message_id: str) -> Tuple[bool, str]:
        msg = Message.objects.filter(id=message_id).first()
        if not msg:
            return False, "Message not found."
        if msg.sender_id != user.id:
            return False, "You can only delete your own messages."

        MessageRepository.soft_delete_message(msg)
        EventDispatcher.publish(MessageDeletedEvent(
            message_id=str(msg.id),
            conversation_id=str(msg.conversation_id)
        ))
        return True, "Message deleted."

class ReceiptService:
    @staticmethod
    def mark_message_read(user: User, message_id: str) -> Tuple[bool, str]:
        msg = Message.objects.filter(id=message_id).first()
        if not msg:
            return False, "Message not found."
            
        members = ConversationSelector.get_members(msg.conversation)
        if user not in members:
            return False, "You are not a member of this conversation."
            
        ReceiptRepository.mark_read(msg, user)
        EventDispatcher.publish(MessageReadEvent(
            message_id=str(msg.id),
            user_id=str(user.id)
        ))
        return True, "Message marked as read."

class TypingService:
    @staticmethod
    def start_typing(user: User, conversation_id: str) -> None:
        key = f"typing:{conversation_id}:{user.id}"
        cache.set(key, True, timeout=5)
        EventDispatcher.publish(TypingStartedEvent(
            conversation_id=conversation_id,
            user_id=str(user.id)
        ))

    @staticmethod
    def stop_typing(user: User, conversation_id: str) -> None:
        key = f"typing:{conversation_id}:{user.id}"
        cache.delete(key)
        EventDispatcher.publish(TypingStoppedEvent(
            conversation_id=conversation_id,
            user_id=str(user.id)
        ))

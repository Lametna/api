from django.contrib.auth import get_user_model
from django.db import transaction
from typing import List, Optional
from .models import Conversation, ConversationMember, Message, MessageReceipt

User = get_user_model()

class ConversationRepository:
    @staticmethod
    @transaction.atomic
    def create_direct_conversation(user1: User, user2: User) -> Conversation:
        conv = Conversation.objects.create(is_group=False)
        ConversationMember.objects.create(conversation=conv, user=user1)
        ConversationMember.objects.create(conversation=conv, user=user2)
        return conv

class MessageRepository:
    @staticmethod
    @transaction.atomic
    def create_message(conversation: Conversation, sender: User, content: str, content_type: str = 'TEXT') -> Message:
        msg = Message.objects.create(
            conversation=conversation, 
            sender=sender, 
            content=content,
            content_type=content_type
        )
        
        # Update conversation last activity
        conversation.last_activity = msg.created_at
        conversation.save(update_fields=['last_activity'])
        
        return msg

    @staticmethod
    def soft_delete_message(message: Message) -> None:
        message.is_deleted = True
        message.save(update_fields=['is_deleted'])

    @staticmethod
    def edit_message(message: Message, new_content: str) -> None:
        message.content = new_content
        message.is_edited = True
        message.save(update_fields=['content', 'is_edited'])

class ReceiptRepository:
    @staticmethod
    def mark_read(message: Message, user: User) -> MessageReceipt:
        receipt, _ = MessageReceipt.objects.get_or_create(message=message, user=user)
        from django.utils import timezone
        receipt.status = MessageReceipt.Status.READ
        receipt.read_at = timezone.now()
        receipt.save(update_fields=['status', 'read_at'])
        return receipt

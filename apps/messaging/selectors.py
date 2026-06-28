from django.contrib.auth import get_user_model
from typing import List, Optional
from .models import Conversation, ConversationMember, Message

User = get_user_model()

class ConversationSelector:
    @staticmethod
    def get_user_conversations(user: User):
        # Return conversations ordered by last_activity
        member_qs = ConversationMember.objects.filter(user=user).select_related('conversation')
        return [m.conversation for m in member_qs.order_by('-conversation__last_activity')]

    @staticmethod
    def get_direct_conversation(user1: User, user2: User) -> Optional[Conversation]:
        # Find a non-group conversation where both users are members
        convs1 = set(ConversationMember.objects.filter(user=user1, conversation__is_group=False).values_list('conversation_id', flat=True))
        convs2 = set(ConversationMember.objects.filter(user=user2, conversation__is_group=False).values_list('conversation_id', flat=True))
        
        common = convs1.intersection(convs2)
        if common:
            return Conversation.objects.filter(id=common.pop()).first()
        return None

    @staticmethod
    def get_members(conversation: Conversation) -> List[User]:
        return [m.user for m in ConversationMember.objects.filter(conversation=conversation).select_related('user')]

class MessageSelector:
    @staticmethod
    def get_conversation_messages(conversation: Conversation, limit=50):
        return Message.objects.filter(conversation=conversation).select_related('sender').order_by('-created_at')[:limit]

from rest_framework import serializers
from .models import Conversation, Message, MessageReceipt
from apps.users.serializers import PublicProfileSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar']

class MessageSerializer(serializers.ModelSerializer):
    sender = BasicUserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content_type', 'content', 'is_edited', 'is_deleted', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    # For a simple list view, we might just return the other member for 1-on-1s
    other_member = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'is_group', 'name', 'last_activity', 'other_member', 'last_message', 'unread_count']

    def get_other_member(self, obj):
        request = self.context.get('request')
        if not request or obj.is_group:
            return None
        # Find the other member
        other = next((m.user for m in obj.members.all() if m.user_id != request.user.id), None)
        return BasicUserSerializer(other).data if other else None

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        return MessageSerializer(msg).data if msg else None
        
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        member_link = obj.members.filter(user=request.user).first()
        return member_link.unread_count if member_link else 0

class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
    content_type = serializers.ChoiceField(choices=Message.ContentType.choices, default='TEXT')

class ConversationCreateSerializer(serializers.Serializer):
    target_user_id = serializers.UUIDField()

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendRequest, Presence

User = get_user_model()

class BasicUserSerializer(serializers.ModelSerializer):
    """Minimal representation of a user for friend lists."""
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar']

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = BasicUserSerializer(read_only=True)
    receiver = BasicUserSerializer(read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']

class FriendActionSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()

class PresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presence
        fields = ['status', 'custom_message', 'current_activity', 'current_game_id', 'last_seen']

class PresenceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presence
        fields = ['status', 'custom_message', 'current_activity', 'current_game_id']
        extra_kwargs = {
            'status': {'required': False},
            'custom_message': {'required': False},
        }

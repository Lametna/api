from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Party, PartyMember, PartyInvitation

User = get_user_model()

class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar']

class PartyMemberSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer(read_only=True)
    is_ready = serializers.SerializerMethodField()
    
    class Meta:
        model = PartyMember
        fields = ['id', 'user', 'role', 'joined_at', 'current_screen', 'is_ready']

    def get_is_ready(self, obj):
        from django.core.cache import cache
        key = f"party:{obj.party_id}:ready:{obj.user_id}"
        return bool(cache.get(key))

class PartySerializer(serializers.ModelSerializer):
    members = PartyMemberSerializer(many=True, read_only=True)
    host = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = ['id', 'name', 'description', 'privacy', 'max_players', 'language', 'is_active', 'current_game_id', 'created_at', 'members', 'host']

    def get_host(self, obj):
        host_member = next((m for m in obj.members.all() if m.role == PartyMember.Role.HOST), None)
        return BasicUserSerializer(host_member.user).data if host_member else None

class PartyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    privacy = serializers.ChoiceField(choices=Party.Privacy.choices, default=Party.Privacy.INVITE_ONLY)
    max_players = serializers.IntegerField(min_value=2, max_value=64, default=4)
    password = serializers.CharField(required=False, allow_blank=True)

class PartyJoinSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, allow_blank=True)

class PartyInviteSerializer(serializers.Serializer):
    target_user_id = serializers.UUIDField()

class PartyReadySerializer(serializers.Serializer):
    is_ready = serializers.BooleanField()

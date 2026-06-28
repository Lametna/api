from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Community, CommunityMember, CommunityPost, CommunityEvent

User = get_user_model()

class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar']

class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'privacy', 'max_members', 'language', 'avatar', 'banner', 'is_active', 'created_at']

class CommunityPostSerializer(serializers.ModelSerializer):
    author = BasicUserSerializer(read_only=True)

    class Meta:
        model = CommunityPost
        fields = ['id', 'author', 'content', 'type', 'is_pinned', 'created_at']

class CommunityCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    privacy = serializers.ChoiceField(choices=Community.Privacy.choices, default=Community.Privacy.PUBLIC)

class CommunityJoinSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, allow_blank=True)

class CommunityEventSerializer(serializers.ModelSerializer):
    creator = BasicUserSerializer(read_only=True)
    
    class Meta:
        model = CommunityEvent
        fields = ['id', 'creator', 'title', 'description', 'start_time', 'end_time', 'game_id', 'party_id', 'created_at']

class PolymorphicFeedSerializer(serializers.Serializer):
    item_type = serializers.CharField()
    
    def to_representation(self, instance):
        base_repr = super().to_representation(instance)
        item_type = instance['item_type']
        
        if item_type == 'POST':
            base_repr['item'] = CommunityPostSerializer(instance['item']).data
        elif item_type == 'EVENT':
            base_repr['item'] = CommunityEventSerializer(instance['item']).data
            
        return base_repr

class PostCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    type = serializers.ChoiceField(choices=CommunityPost.Type.choices, default=CommunityPost.Type.TEXT)

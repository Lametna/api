from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['banner', 'biography', 'updated_at']

class UserMeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'avatar',
            'language', 'theme', 'timezone', 'country',
            'is_verified', 'created_at', 'profile'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at']

class UserMeUpdateSerializer(serializers.ModelSerializer):
    banner = serializers.URLField(required=False)
    biography = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = User
        fields = [
            'display_name', 'avatar', 'language', 'theme', 
            'timezone', 'country', 'banner', 'biography', 'birth_month', 'accent_color', 'website', 'social_links'
        ]

class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import UserPreference
        model = UserPreference
        exclude = ['user', 'updated_at']

class PrivacySerializer(serializers.ModelSerializer):
    class Meta:
        from .models import UserPrivacy
        model = UserPrivacy
        exclude = ['user', 'updated_at']

class PublicProfileSerializer(serializers.Serializer):
    """
    Dynamically serialized based on Privacy rules. 
    This is just a base schema for OpenAPI docs. Actual response varies.
    """
    id = serializers.UUIDField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar = serializers.URLField()
    banner = serializers.URLField()
    biography = serializers.CharField()
    country = serializers.CharField(required=False)
    favorite_games = serializers.ListField(child=serializers.CharField(), required=False)

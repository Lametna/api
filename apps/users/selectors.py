from django.contrib.auth import get_user_model
from typing import Optional
from .models import Profile

User = get_user_model()

class UserSelector:
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return User.objects.filter(email=email).first()

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        return User.objects.filter(username=username).first()

    @staticmethod
    def get_by_id(user_id: str) -> Optional[User]:
        return User.objects.filter(id=user_id).first()

class ProfileSelector:
    @staticmethod
    def get_profile_by_user(user: User) -> Optional[Profile]:
        return Profile.objects.filter(user=user).first()

class PreferenceSelector:
    @staticmethod
    def get_preferences(user: User):
        from .models import UserPreference
        pref, _ = UserPreference.objects.get_or_create(user=user)
        return pref

class PrivacySelector:
    @staticmethod
    def get_privacy(user: User):
        from .models import UserPrivacy
        priv, _ = UserPrivacy.objects.get_or_create(user=user)
        return priv

class FavoriteSelector:
    @staticmethod
    def get_favorite_games(user: User):
        from .models import FavoriteGame
        return list(FavoriteGame.objects.filter(user=user).values_list('game_id', flat=True))

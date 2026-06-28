from django.contrib.auth import get_user_model
from typing import Dict, Any, Optional
from .models import Profile

User = get_user_model()

class UserRepository:
    @staticmethod
    def create_user(email: str, username: str, password: str, **extra_fields: Any) -> User:
        return User.objects.create_user(email=email, username=username, password=password, **extra_fields)

    @staticmethod
    def update_user(user: User, data: Dict[str, Any]) -> User:
        for field, value in data.items():
            setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    def deactivate_user(user: User) -> None:
        user.is_active = False
        user.save(update_fields=['is_active'])

class ProfileRepository:
    @staticmethod
    def update_profile(profile: Profile, data: Dict[str, Any]) -> Profile:
        for field, value in data.items():
            setattr(profile, field, value)
        profile.save()
        return profile

class PreferenceRepository:
    @staticmethod
    def update_preferences(preference, data: Dict[str, Any]):
        for field, value in data.items():
            setattr(preference, field, value)
        preference.save()
        return preference

class PrivacyRepository:
    @staticmethod
    def update_privacy(privacy, data: Dict[str, Any]):
        for field, value in data.items():
            setattr(privacy, field, value)
        privacy.save()
        return privacy

class FavoriteRepository:
    @staticmethod
    def add_favorite_game(user: User, game_id: str):
        from .models import FavoriteGame
        return FavoriteGame.objects.get_or_create(user=user, game_id=game_id)
        
    @staticmethod
    def remove_favorite_game(user: User, game_id: str):
        from .models import FavoriteGame
        FavoriteGame.objects.filter(user=user, game_id=game_id).delete()

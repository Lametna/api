from typing import Tuple, Dict, Any
from django.contrib.auth import get_user_model
from django.db import transaction
from .repositories import UserRepository
from apps.authentication.services import OTPService, MockEmailService
from apps.authentication.models import VerificationCode

User = get_user_model()

class RegistrationService:
    @staticmethod
    @transaction.atomic
    def register_user(data: Dict[str, Any]) -> Tuple[bool, Any, str]:
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if User.objects.filter(email=email).exists():
            return False, None, "Email is already registered."
        
        if User.objects.filter(username=username).exists():
            return False, None, "Username is already taken."

        user = UserRepository.create_user(
            email=email,
            username=username,
            password=password,
            display_name=data.get('display_name', '')
        )

        # Trigger Registration OTP
        otp = OTPService.create_otp(user, VerificationCode.Purpose.REGISTRATION)
        MockEmailService.send_verification_email(user.email, otp.code)

        return True, {"user_id": user.id, "email": user.email}, "User registered successfully. Please verify your email."

    @staticmethod
    def verify_registration(user: User, code: str) -> Tuple[bool, str]:
        if user.is_verified:
            return False, "User is already verified."

        is_valid, msg = OTPService.validate_otp(user, VerificationCode.Purpose.REGISTRATION, code)
        if not is_valid:
            return False, msg

        # Mark user as verified
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        
        return True, "Account verified successfully. You may now log in."

class PrivacyService:
    @staticmethod
    def apply_visibility_rules(viewer: User, target_user: User, profile_data: Dict[str, Any], privacy_settings) -> Dict[str, Any]:
        """
        Strips fields from profile_data based on privacy rules and viewer relationship.
        """
        # If viewing own profile, return everything
        if viewer.is_authenticated and viewer.id == target_user.id:
            return profile_data

        # Check overarching visibility
        if privacy_settings.profile_visibility == 'PRIVATE':
            return {"message": "This profile is private."}
            
        if privacy_settings.profile_visibility == 'FRIENDS_ONLY':
            # Placeholder for Friends check
            is_friend = False 
            if not is_friend:
                return {"message": "This profile is visible to friends only."}

        # Apply granular field rules
        if privacy_settings.hide_country and 'country' in profile_data:
            profile_data.pop('country')
            
        if privacy_settings.hide_activity and 'activity' in profile_data:
            profile_data.pop('activity')
            
        if privacy_settings.hide_statistics and 'statistics' in profile_data:
            profile_data.pop('statistics')
            
        if privacy_settings.hide_favorite_games and 'favorite_games' in profile_data:
            profile_data.pop('favorite_games')

        return profile_data

class ProfileCompletionService:
    @staticmethod
    def calculate_completion(user: User, profile: Any) -> int:
        fields_to_check = [
            user.is_verified,
            bool(user.display_name),
            bool(user.avatar),
            bool(user.country),
            bool(user.language),
            bool(profile.banner_url),
            bool(profile.biography),
            bool(profile.birth_month)
        ]
        completed = sum(1 for field in fields_to_check if field)
        total = len(fields_to_check)
        
        return int((completed / total) * 100)

class MediaStorageService:
    @staticmethod
    def save_file(file, user_id: str, media_type: str) -> str:
        """
        Storage abstraction. Currently saves to local disk and returns URL path.
        In the future, this swaps to AWS S3 / django-storages.
        """
        import os
        from django.core.files.storage import default_storage
        from django.conf import settings
        
        path = f"{media_type}/{user_id}/{file.name}"
        saved_path = default_storage.save(path, file)
        
        # Return URL-friendly path
        return f"{settings.MEDIA_URL}{saved_path}"

class AvatarService:
    @staticmethod
    def upload_avatar(user: User, file) -> str:
        from .validators import validate_avatar_image
        validate_avatar_image(file)
        
        url = MediaStorageService.save_file(file, user.id, "avatars")
        user.avatar = url
        user.save(update_fields=['avatar'])
        return url

class BannerService:
    @staticmethod
    def upload_banner(user: User, profile, file) -> str:
        from .validators import validate_banner_image
        validate_banner_image(file)
        
        url = MediaStorageService.save_file(file, user.id, "banners")
        profile.banner_url = url
        profile.save(update_fields=['banner_url'])
        return url

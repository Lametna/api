from typing import Optional, List
from django.utils import timezone
from .models import VerificationCode, Device, LoginHistory
from django.contrib.auth import get_user_model

User = get_user_model()

class OTPSelector:
    @staticmethod
    def get_latest_valid_otp(user: User, purpose: str) -> Optional[VerificationCode]:
        return VerificationCode.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()


class DeviceSelector:
    @staticmethod
    def get_active_device_by_fingerprint(user: User, fingerprint: str) -> Optional[Device]:
        return Device.objects.filter(
            user=user,
            fingerprint=fingerprint,
            is_active=True
        ).first()

    @staticmethod
    def get_user_active_devices(user: User) -> List[Device]:
        return list(Device.objects.filter(user=user, is_active=True))

    @staticmethod
    def get_device_by_id(device_id: str, user: User) -> Optional[Device]:
        return Device.objects.filter(id=device_id, user=user, is_active=True).first()


class LoginHistorySelector:
    @staticmethod
    def get_user_login_history(user: User, limit: int = 50) -> List[LoginHistory]:
        return list(LoginHistory.objects.filter(user=user)[:limit])

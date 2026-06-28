from typing import Optional, Dict, Any
from django.utils import timezone
from .models import VerificationCode, Device, LoginHistory
from django.contrib.auth import get_user_model

User = get_user_model()

class OTPRepository:
    @staticmethod
    def create_otp(user: User, code: str, purpose: str, expires_at: timezone.datetime) -> VerificationCode:
        return VerificationCode.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=expires_at
        )

    @staticmethod
    def mark_used(otp: VerificationCode) -> None:
        otp.is_used = True
        otp.save(update_fields=['is_used'])

    @staticmethod
    def increment_attempts(otp: VerificationCode) -> None:
        otp.attempts += 1
        otp.save(update_fields=['attempts'])


class DeviceRepository:
    @staticmethod
    def create_device(user: User, fingerprint: str, **kwargs: Any) -> Device:
        return Device.objects.create(user=user, fingerprint=fingerprint, **kwargs)

    @staticmethod
    def update_last_used(device: Device) -> None:
        device.last_used = timezone.now()
        device.save(update_fields=['last_used'])

    @staticmethod
    def mark_trusted(device: Device) -> None:
        device.is_trusted = True
        device.save(update_fields=['is_trusted'])

    @staticmethod
    def deactivate_device(device: Device) -> None:
        device.is_active = False
        device.save(update_fields=['is_active'])


class LoginHistoryRepository:
    @staticmethod
    def record_login(user: User, is_success: bool, **kwargs: Any) -> LoginHistory:
        return LoginHistory.objects.create(
            user=user,
            is_success=is_success,
            **kwargs
        )

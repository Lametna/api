import random
import string
import logging
from typing import Tuple, Optional, Any
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

from .models import VerificationCode, Device, LoginHistory
from .repositories import OTPRepository, DeviceRepository, LoginHistoryRepository
from .selectors import OTPSelector, DeviceSelector

logger = logging.getLogger(__name__)
User = get_user_model()

class MockEmailService:
    @staticmethod
    def send_verification_email(email: str, code: str) -> None:
        logger.info(f"========== EMAIL SENT ==========")
        logger.info(f"To: {email}")
        logger.info(f"Verification Code: {code}")
        logger.info(f"================================")

    @staticmethod
    def send_new_device_email(email: str, code: str, device_name: str) -> None:
        logger.info(f"========== SECURITY ALERT ==========")
        logger.info(f"To: {email}")
        logger.info(f"New login from {device_name}.")
        logger.info(f"Verification Code: {code}")
        logger.info(f"====================================")


class OTPService:
    MAX_ATTEMPTS = 5
    EXPIRY_MINUTES = 15

    @staticmethod
    def generate_code() -> str:
        return ''.join(random.choices(string.digits, k=6))

    @classmethod
    def create_otp(cls, user: User, purpose: str) -> VerificationCode:
        # Invalidate existing OTPs for this purpose
        VerificationCode.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
        
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=cls.EXPIRY_MINUTES)
        
        return OTPRepository.create_otp(user, code, purpose, expires_at)

    @classmethod
    def validate_otp(cls, user: User, purpose: str, code: str) -> Tuple[bool, str]:
        otp = OTPSelector.get_latest_valid_otp(user, purpose)
        
        if not otp:
            return False, "No valid or unexpired OTP found."
            
        if otp.attempts >= cls.MAX_ATTEMPTS:
            OTPRepository.mark_used(otp)
            return False, "Maximum attempts reached. Please request a new code."

        if otp.code != code:
            OTPRepository.increment_attempts(otp)
            return False, "Invalid verification code."

        OTPRepository.mark_used(otp)
        return True, "Verification successful."


class DeviceService:
    @staticmethod
    def generate_fingerprint(user_agent: str, ip_address: str) -> str:
        """
        Simple fingerprinting for the MVP. In a real app, use a client-side library.
        """
        import hashlib
        raw = f"{user_agent}|{ip_address}".encode('utf-8')
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def evaluate_device_trust(cls, user: User, request_meta: dict) -> Tuple[bool, Device]:
        user_agent = request_meta.get('HTTP_USER_AGENT', 'Unknown')
        ip_address = request_meta.get('REMOTE_ADDR', '0.0.0.0')
        fingerprint = cls.generate_fingerprint(user_agent, ip_address)

        device = DeviceSelector.get_active_device_by_fingerprint(user, fingerprint)
        
        if not device:
            # Parse simple OS/Browser from user_agent (placeholder logic)
            os_name = "Windows" if "Windows" in user_agent else "Mac" if "Mac" in user_agent else "Unknown OS"
            browser = "Chrome" if "Chrome" in user_agent else "Firefox" if "Firefox" in user_agent else "Unknown Browser"
            device_name = f"{os_name} - {browser}"

            device = DeviceRepository.create_device(
                user=user, 
                fingerprint=fingerprint,
                device_name=device_name,
                browser=browser,
                os=os_name,
                ip_address=ip_address
            )

        DeviceRepository.update_last_used(device)
        return device.is_trusted, device


class AuthService:
    @staticmethod
    def login(email: str, password: str, request_meta: dict) -> Tuple[bool, Any, str]:
        """
        Returns (success, data, error_message)
        """
        user = User.objects.filter(email=email).first()
        if not user:
            return False, None, "Invalid email or password."

        if not check_password(password, user.password):
            LoginHistoryRepository.record_login(user, False, failure_reason="Invalid password")
            return False, None, "Invalid email or password."

        if not user.is_active:
            return False, None, "Account is deactivated."

        if not user.is_verified:
            # Resend registration OTP
            otp = OTPService.create_otp(user, VerificationCode.Purpose.REGISTRATION)
            MockEmailService.send_verification_email(user.email, otp.code)
            return False, {"requires_verification": True, "purpose": "REGISTRATION"}, "Email not verified. A new code has been sent."

        # Evaluate Device Trust
        is_trusted, device = DeviceService.evaluate_device_trust(user, request_meta)
        
        if not is_trusted:
            # Trigger New Device Verification Flow
            otp = OTPService.create_otp(user, VerificationCode.Purpose.DEVICE_VERIFICATION)
            MockEmailService.send_new_device_email(user.email, otp.code, device.device_name)
            LoginHistoryRepository.record_login(user, False, device=device, failure_reason="Untrusted device OTP required")
            return False, {"requires_verification": True, "purpose": "DEVICE_VERIFICATION", "device_id": device.id}, "Unrecognized device. Please verify your email."

        # Successful Login
        LoginHistoryRepository.record_login(user, True, device=device, ip_address=device.ip_address, browser=device.browser, os=device.os)
        
        refresh = RefreshToken.for_user(user)
        
        return True, {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }, "Login successful."

    @staticmethod
    def verify_device_login(user: User, code: str, device_id: str) -> Tuple[bool, Any, str]:
        device = DeviceSelector.get_device_by_id(device_id, user)
        if not device:
            return False, None, "Device not found."

        is_valid, msg = OTPService.validate_otp(user, VerificationCode.Purpose.DEVICE_VERIFICATION, code)
        if not is_valid:
            return False, None, msg

        DeviceRepository.mark_trusted(device)
        
        LoginHistoryRepository.record_login(user, True, device=device, ip_address=device.ip_address)
        refresh = RefreshToken.for_user(user)
        
        return True, {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }, "Device verified successfully."

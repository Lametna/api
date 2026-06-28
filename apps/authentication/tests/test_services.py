import pytest
from django.contrib.auth import get_user_model
from apps.authentication.services import OTPService, DeviceService, AuthService
from apps.authentication.models import VerificationCode

User = get_user_model()

@pytest.mark.django_db
class TestOTPService:
    def test_generate_otp(self):
        user = User.objects.create_user(username='test', email='test@example.com', password='pwd')
        otp = OTPService.create_otp(user, VerificationCode.Purpose.REGISTRATION)
        
        assert len(otp.code) == 6
        assert otp.purpose == VerificationCode.Purpose.REGISTRATION
        assert not otp.is_used

    def test_validate_otp_success(self):
        user = User.objects.create_user(username='test2', email='test2@example.com', password='pwd')
        otp = OTPService.create_otp(user, VerificationCode.Purpose.REGISTRATION)
        
        is_valid, msg = OTPService.validate_otp(user, VerificationCode.Purpose.REGISTRATION, otp.code)
        assert is_valid
        
        # Verify it can't be used twice
        otp.refresh_from_db()
        assert otp.is_used

    def test_validate_otp_failure(self):
        user = User.objects.create_user(username='test3', email='test3@example.com', password='pwd')
        OTPService.create_otp(user, VerificationCode.Purpose.REGISTRATION)
        
        is_valid, msg = OTPService.validate_otp(user, VerificationCode.Purpose.REGISTRATION, "000000")
        assert not is_valid

@pytest.mark.django_db
class TestDeviceService:
    def test_evaluate_device_trust_new_device(self):
        user = User.objects.create_user(username='test4', email='test4@example.com', password='pwd')
        meta = {'HTTP_USER_AGENT': 'Mozilla/5.0 Windows', 'REMOTE_ADDR': '192.168.1.1'}
        
        is_trusted, device = DeviceService.evaluate_device_trust(user, meta)
        assert not is_trusted
        assert device.device_name == 'Windows - Unknown Browser'
        assert device.ip_address == '192.168.1.1'

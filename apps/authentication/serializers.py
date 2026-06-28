from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, min_length=3)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    device_id = serializers.CharField(required=False, help_text="Required if verifying a new device login")

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=['REGISTRATION', 'DEVICE_VERIFICATION', 'PASSWORD_RESET'])

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

class DeviceSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    device_name = serializers.CharField(read_only=True)
    browser = serializers.CharField(read_only=True)
    os = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    is_trusted = serializers.BooleanField(read_only=True)
    last_used = serializers.DateTimeField(read_only=True)

class LoginHistorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    browser = serializers.CharField(read_only=True)
    os = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    is_success = serializers.BooleanField(read_only=True)
    failure_reason = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

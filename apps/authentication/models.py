from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel

class VerificationCode(BaseModel):
    class Purpose(models.TextChoices):
        REGISTRATION = 'REGISTRATION', _('Registration')
        DEVICE_VERIFICATION = 'DEVICE_VERIFICATION', _('Device Verification')
        PASSWORD_RESET = 'PASSWORD_RESET', _('Password Reset')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, choices=Purpose.choices)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
        ]

    def __str__(self):
        return f"{self.purpose} for {self.user.email}"


class Device(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fingerprint = models.CharField(max_length=255, db_index=True)
    
    is_trusted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['user', 'fingerprint']),
        ]

    def __str__(self):
        return f"{self.device_name} ({self.user.email})"


class LoginHistory(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='login_history')
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text="Placeholder for GeoIP")
    
    is_success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "Success" if self.is_success else "Failed"
        return f"{status} login by {self.user.email} at {self.created_at}"

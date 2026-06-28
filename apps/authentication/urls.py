from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, VerifyEmailView, VerifyDeviceLoginView

app_name = 'authentication'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/verify-device/', VerifyDeviceLoginView.as_view(), name='login_verify_device'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Note: logout, password endpoints are omitted for brevity in this MVP step
]

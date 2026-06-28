from django.urls import path
from .views import (
    UserMeView, UserDevicesView, UserSessionsView,
    PreferencesView, PrivacySettingsView, AvatarUploadView, 
    BannerUploadView, PublicProfileView
)

app_name = 'users'

urlpatterns = [
    path('me/', UserMeView.as_view(), name='user_me'),
    path('me/devices/', UserDevicesView.as_view(), name='user_devices'),
    path('me/sessions/', UserSessionsView.as_view(), name='user_sessions'),
    
    path('profile/preferences/', PreferencesView.as_view(), name='preferences'),
    path('profile/privacy/', PrivacySettingsView.as_view(), name='privacy'),
    path('profile/avatar/', AvatarUploadView.as_view(), name='avatar_upload'),
    path('profile/banner/', BannerUploadView.as_view(), name='banner_upload'),
    path('profile/<str:username>/', PublicProfileView.as_view(), name='public_profile'),
]

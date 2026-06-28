from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema

from .serializers import UserMeSerializer, UserMeUpdateSerializer
from .repositories import UserRepository, ProfileRepository
from .selectors import ProfileSelector
from apps.authentication.selectors import DeviceSelector, LoginHistorySelector
from apps.authentication.serializers import DeviceSerializer, LoginHistorySerializer

class UserMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserMeSerializer})
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(request=UserMeUpdateSerializer, responses={200: UserMeSerializer})
    def patch(self, request):
        serializer = UserMeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        profile_data = {
            k: data.pop(k) for k in ['banner', 'biography'] if k in data
        }

        user = UserRepository.update_user(request.user, data)
        
        if profile_data:
            profile = ProfileSelector.get_profile_by_user(user)
            if profile:
                ProfileRepository.update_profile(profile, profile_data)

        return Response({"success": True, "data": UserMeSerializer(user).data})

    def delete(self, request):
        UserRepository.deactivate_user(request.user)
        return Response({"success": True, "message": "Account deactivated successfully."})


class UserDevicesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: DeviceSerializer(many=True)})
    def get(self, request):
        devices = DeviceSelector.get_user_active_devices(request.user)
        serializer = DeviceSerializer(devices, many=True)
        return Response({"success": True, "data": serializer.data})


class UserSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: LoginHistorySerializer(many=True)})
    def get(self, request):
        history = LoginHistorySelector.get_user_login_history(request.user)
        serializer = LoginHistorySerializer(history, many=True)
        return Response({"success": True, "data": serializer.data})

from .serializers import PreferencesSerializer, PrivacySerializer, PublicProfileSerializer
from .selectors import PreferenceSelector, PrivacySelector, FavoriteSelector
from .repositories import PreferenceRepository, PrivacyRepository
from .services import AvatarService, BannerService, PrivacyService, ProfileCompletionService

class PreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PreferencesSerializer})
    def get(self, request):
        prefs = PreferenceSelector.get_preferences(request.user)
        return Response({"success": True, "data": PreferencesSerializer(prefs).data})

    @extend_schema(request=PreferencesSerializer, responses={200: PreferencesSerializer})
    def patch(self, request):
        prefs = PreferenceSelector.get_preferences(request.user)
        serializer = PreferencesSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        PreferenceRepository.update_preferences(prefs, serializer.validated_data)
        return Response({"success": True, "data": serializer.data})

class PrivacySettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PrivacySerializer})
    def get(self, request):
        priv = PrivacySelector.get_privacy(request.user)
        return Response({"success": True, "data": PrivacySerializer(priv).data})

    @extend_schema(request=PrivacySerializer, responses={200: PrivacySerializer})
    def patch(self, request):
        priv = PrivacySelector.get_privacy(request.user)
        serializer = PrivacySerializer(priv, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        PrivacyRepository.update_privacy(priv, serializer.validated_data)
        return Response({"success": True, "data": serializer.data})

class AvatarUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(request={'multipart/form-data': {'type': 'object', 'properties': {'avatar': {'type': 'string', 'format': 'binary'}}}})
    def post(self, request):
        if 'avatar' not in request.FILES:
            return Response({"success": False, "message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
        url = AvatarService.upload_avatar(request.user, request.FILES['avatar'])
        return Response({"success": True, "avatar_url": url})
        
    def delete(self, request):
        request.user.avatar = ""
        request.user.save(update_fields=['avatar'])
        return Response({"success": True, "message": "Avatar removed."})

class BannerUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request={'multipart/form-data': {'type': 'object', 'properties': {'banner': {'type': 'string', 'format': 'binary'}}}})
    def post(self, request):
        if 'banner' not in request.FILES:
            return Response({"success": False, "message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
        profile = ProfileSelector.get_profile_by_user(request.user)
        url = BannerService.upload_banner(request.user, profile, request.FILES['banner'])
        return Response({"success": True, "banner_url": url})

    def delete(self, request):
        profile = ProfileSelector.get_profile_by_user(request.user)
        profile.banner_url = ""
        profile.save(update_fields=['banner_url'])
        return Response({"success": True, "message": "Banner removed."})

class PublicProfileView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @extend_schema(responses={200: PublicProfileSerializer})
    def get(self, request, username):
        from .selectors import UserSelector
        target_user = UserSelector.get_by_username(username)
        if not target_user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        target_profile = ProfileSelector.get_profile_by_user(target_user)
        target_privacy = PrivacySelector.get_privacy(target_user)
        
        # Build base raw profile data
        raw_data = {
            "id": str(target_user.id),
            "username": target_user.username,
            "display_name": target_user.display_name,
            "avatar": target_user.avatar,
            "banner": target_profile.banner_url if target_profile else "",
            "biography": target_profile.biography if target_profile else "",
            "country": target_user.country,
            "favorite_games": FavoriteSelector.get_favorite_games(target_user)
        }
        
        # Apply privacy masking
        masked_data = PrivacyService.apply_visibility_rules(request.user, target_user, raw_data, target_privacy)
        
        return Response({"success": True, "data": masked_data})

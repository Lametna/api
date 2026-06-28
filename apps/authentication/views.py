from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from .serializers import (
    RegisterSerializer, LoginSerializer, OTPVerifySerializer, ResendOTPSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from apps.users.services import RegistrationService
from .services import AuthService, OTPService, MockEmailService
from .models import VerificationCode
from apps.users.selectors import UserSelector

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: inline_serializer('RegisterResponse', fields={'success': serializers.BooleanField(), 'message': serializers.CharField()})})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, data, msg = RegistrationService.register_user(serializer.validated_data)
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"success": True, "message": msg}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success, data, msg = AuthService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            request_meta=request.META
        )

        if not success:
            if data and data.get("requires_verification"):
                return Response({
                    "success": False,
                    "message": msg,
                    "requires_verification": True,
                    "device_id": data.get('device_id')
                }, status=status.HTTP_403_FORBIDDEN)
            return Response({"success": False, "message": msg}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"success": True, "data": data, "message": msg})


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=OTPVerifySerializer)
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = UserSelector.get_by_email(serializer.validated_data['email'])
        if not user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        success, msg = RegistrationService.verify_registration(user, serializer.validated_data['code'])
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True, "message": msg})


class VerifyDeviceLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=OTPVerifySerializer)
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserSelector.get_by_email(serializer.validated_data['email'])
        if not user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        device_id = serializer.validated_data.get('device_id')
        if not device_id:
            return Response({"success": False, "message": "device_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        success, data, msg = AuthService.verify_device_login(user, serializer.validated_data['code'], device_id)
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"success": True, "data": data, "message": msg})

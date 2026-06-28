from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_spectacular.utils import extend_schema

from .services import FeatureFlagService

class FeatureFlagsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        """
        Returns a dictionary of all feature flags and whether they are enabled
        for the currently authenticated user.
        """
        flags = FeatureFlagService.get_all_flags_for_user(request.user)
        return Response({"success": True, "data": flags})

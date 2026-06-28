from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_spectacular.utils import extend_schema
from apps.games.models import SecretWordPack, SecretCategory
from .serializers import SecretWordPackSerializer, SecretCategorySerializer
from .plugin import SpyPlugin

class SpyPacksView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: SecretWordPackSerializer(many=True)})
    def get(self, request):
        packs = SecretWordPack.objects.filter(is_active=True).prefetch_related('categories')
        return Response({"success": True, "data": SecretWordPackSerializer(packs, many=True).data})

class SpyCategoriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: SecretCategorySerializer(many=True)})
    def get(self, request):
        categories = SecretCategory.objects.filter(is_active=True)
        return Response({"success": True, "data": SecretCategorySerializer(categories, many=True).data})

class SpyConfigSchemaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        # Expose the configuration options directly from the plugin metadata
        plugin = SpyPlugin()
        return Response({"success": True, "data": plugin.metadata})

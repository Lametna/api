from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from .services import NotificationService, NotificationPreferenceService
from .selectors import NotificationSelector, NotificationPreferenceSelector

class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: NotificationSerializer(many=True)})
    def get(self, request):
        notifs = NotificationSelector.get_user_notifications(request.user)
        return Response({
            "success": True, 
            "unread_count": NotificationSelector.get_unread_count(request.user),
            "data": NotificationSerializer(notifs, many=True).data
        })

class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, notification_id):
        success = NotificationService.mark_as_read(request.user, notification_id)
        return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_404_NOT_FOUND)

    def delete(self, request, notification_id):
        success = NotificationService.delete_notification(request.user, notification_id)
        return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_404_NOT_FOUND)

class NotificationReadAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)
        return Response({"success": True, "marked_read": count})

class NotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: NotificationPreferenceSerializer})
    def get(self, request):
        prefs = NotificationPreferenceSelector.get_preferences(request.user)
        return Response({"success": True, "data": NotificationPreferenceSerializer(prefs).data})

    @extend_schema(request=NotificationPreferenceSerializer, responses={200: NotificationPreferenceSerializer})
    def patch(self, request):
        serializer = NotificationPreferenceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        prefs = NotificationPreferenceService.update_preferences(request.user, **serializer.validated_data)
        return Response({"success": True, "data": NotificationPreferenceSerializer(prefs).data})

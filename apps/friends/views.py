from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from django.db.models import Q

from .serializers import (
    BasicUserSerializer, FriendRequestSerializer, FriendActionSerializer, 
    PresenceSerializer, PresenceUpdateSerializer
)
from .services import (
    FriendService, FriendRequestService, BlockService, 
    SuggestionService, PresenceService
)
from .selectors import FriendSelector, BlockSelector, PresenceSelector

User = get_user_model()

class FriendsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: BasicUserSerializer(many=True)})
    def get(self, request):
        friends = FriendSelector.get_friends(request.user)
        return Response({"success": True, "data": BasicUserSerializer(friends, many=True).data})

class FriendRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, user_id):
        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        success, msg = FriendService.remove_friend(request.user, target_user)
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=FriendActionSerializer)
    def post(self, request):
        serializer = FriendActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_user = User.objects.filter(id=serializer.validated_data['user_id']).first()
        if not target_user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        success, msg = FriendRequestService.send_request(request.user, target_user)
        return Response({"success": success, "message": msg}, status=status.HTTP_201_CREATED if success else status.HTTP_400_BAD_REQUEST)

class FriendRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_target(self, user_id):
        return User.objects.filter(id=user_id).first()

    @extend_schema(request=FriendActionSerializer)
    def post(self, request, action):
        serializer = FriendActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user = self._get_target(serializer.validated_data['user_id'])
        
        if not target_user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            success, msg = FriendRequestService.accept_request(target_user, request.user) # Target is sender
        elif action == 'decline':
            success, msg = FriendRequestService.decline_request(target_user, request.user) # Target is sender
        elif action == 'cancel':
            success, msg = FriendRequestService.cancel_request(request.user, target_user) # We are sender
        else:
            return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class PendingRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: FriendRequestSerializer(many=True)})
    def get(self, request):
        received = FriendSelector.get_pending_requests_received(request.user)
        return Response({"success": True, "data": FriendRequestSerializer(received, many=True).data})

class BlockedUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: BasicUserSerializer(many=True)})
    def get(self, request):
        blocked = BlockSelector.get_blocked_users(request.user)
        return Response({"success": True, "data": BasicUserSerializer(blocked, many=True).data})

    @extend_schema(request=FriendActionSerializer)
    def post(self, request):
        serializer = FriendActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user = User.objects.filter(id=serializer.validated_data['user_id']).first()
        if not target_user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        success, msg = BlockService.block_user(request.user, target_user)
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class UnblockUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, user_id):
        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        success, msg = BlockService.unblock_user(request.user, target_user)
        return Response({"success": success, "message": msg})

class SearchFriendsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: BasicUserSerializer(many=True)})
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response({"success": True, "data": []})
            
        users = User.objects.filter(Q(username__icontains=query) | Q(display_name__icontains=query))[:20]
        # Hide blocked users
        blocked_ids = [u.id for u in BlockSelector.get_blocked_users(request.user)]
        filtered_users = [u for u in users if u.id not in blocked_ids and u.id != request.user.id]
        
        return Response({"success": True, "data": BasicUserSerializer(filtered_users, many=True).data})

class SuggestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: BasicUserSerializer(many=True)})
    def get(self, request):
        suggestions = SuggestionService.get_suggestions(request.user)
        return Response({"success": True, "data": BasicUserSerializer(suggestions, many=True).data})

class PresenceMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PresenceSerializer})
    def get(self, request):
        presence = PresenceSelector.get_presence(request.user)
        presence.status = PresenceService.get_user_status(request.user.id)
        return Response({"success": True, "data": PresenceSerializer(presence).data})

    @extend_schema(request=PresenceUpdateSerializer, responses={200: PresenceSerializer})
    def patch(self, request):
        from .repositories import PresenceRepository
        serializer = PresenceUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        presence = PresenceRepository.update_presence(request.user, **serializer.validated_data)
        
        # If they manually set status to invisible, override Redis logic
        if serializer.validated_data.get('status') in ['INVISIBLE', 'OFFLINE']:
            PresenceService.set_offline(request.user.id)
            
        return Response({"success": True, "data": PresenceSerializer(presence).data})

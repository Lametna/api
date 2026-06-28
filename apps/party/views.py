from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from .serializers import PartySerializer, PartyCreateSerializer, PartyJoinSerializer, PartyInviteSerializer, PartyReadySerializer
from .services import PartyService, PartyMembershipService, InvitationService, ReadyService, HostMigrationService
from .selectors import PartySelector

User = get_user_model()

class PartyListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PartySerializer(many=True)})
    def get(self, request):
        parties = PartySelector.get_public_parties()
        return Response({"success": True, "data": PartySerializer(parties, many=True).data})

    @extend_schema(request=PartyCreateSerializer, responses={201: PartySerializer})
    def post(self, request):
        serializer = PartyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, party, msg = PartyService.create_party(
            host=request.user, 
            name=serializer.validated_data['name'],
            privacy=serializer.validated_data['privacy'],
            max_players=serializer.validated_data.get('max_players', 4),
            password=serializer.validated_data.get('password')
        )
        
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "data": PartySerializer(party).data}, status=status.HTTP_201_CREATED)

class PartyDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PartySerializer})
    def get(self, request, party_id):
        party = PartySelector.get_party(party_id)
        if not party:
            return Response({"success": False, "message": "Party not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": PartySerializer(party).data})

    def delete(self, request, party_id):
        success, msg = PartyService.disband_party(request.user, party_id)
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class PartyJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PartyJoinSerializer)
    def post(self, request, party_id):
        serializer = PartyJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success, msg = PartyMembershipService.join_party(request.user, str(party_id), serializer.validated_data.get('password'))
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class PartyLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, party_id):
        success, msg = PartyMembershipService.leave_party(request.user, str(party_id))
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class PartyInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PartyInviteSerializer)
    def post(self, request, party_id):
        serializer = PartyInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target = User.objects.filter(id=serializer.validated_data['target_user_id']).first()
        if not target:
            return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        success, msg = InvitationService.send_invite(request.user, target, str(party_id))
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class PartyReadyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PartyReadySerializer)
    def post(self, request, party_id):
        serializer = PartyReadySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ReadyService.set_ready(str(party_id), str(request.user.id), serializer.validated_data['is_ready'])
        return Response({"success": True})

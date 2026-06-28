from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .serializers import GameSerializer, MatchSerializer, MatchCreateSerializer, ScoreSerializer
from .services import MatchService
from .selectors import GameSelector, MatchSelector, ScoreSelector

class GameListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: GameSerializer(many=True)})
    def get(self, request):
        games = GameSelector.get_active_games()
        return Response({"success": True, "data": GameSerializer(games, many=True).data})

class MatchListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=MatchCreateSerializer, responses={201: MatchSerializer})
    def post(self, request):
        serializer = MatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, match, msg = MatchService.create_match(
            host=request.user, 
            game_id=serializer.validated_data['game_id'], 
            party_id=serializer.validated_data.get('party_id'),
            config=serializer.validated_data.get('configuration')
        )
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "data": MatchSerializer(match).data}, status=status.HTTP_201_CREATED)

class MatchDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MatchSerializer})
    def get(self, request, pk):
        match = MatchSelector.get_match(pk)
        if not match:
            return Response({"success": False, "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": MatchSerializer(match).data})

class MatchActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        if action == 'start':
            success, msg = MatchService.start_match(request.user, pk)
        elif action == 'join':
            success, msg = MatchService.join_match(request.user, pk)
        else:
            return Response({"success": False, "message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class MatchScoresView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: ScoreSerializer(many=True)})
    def get(self, request, pk):
        match = MatchSelector.get_match(pk)
        if not match:
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
            
        scores = ScoreSelector.get_scores(match)
        return Response({"success": True, "data": ScoreSerializer(scores, many=True).data})

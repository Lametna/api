from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .serializers import (
    LeaderboardSerializer, LeaderboardEntrySerializer, PlayerRatingSerializer,
    SeasonSerializer, LiveEventSerializer, TournamentSerializer, 
    TournamentParticipantSerializer, TournamentMatchSerializer, 
    CompetitiveStatisticsSerializer, TournamentRegisterRequestSerializer
)
from .selectors import (
    LeaderboardSelector, RankingSelector, SeasonSelector, EventSelector,
    TournamentSelector, StatisticsSelector
)
from .services import TournamentService

# --- Leaderboards ---
class LeaderboardListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: LeaderboardSerializer(many=True)})
    def get(self, request):
        lbs = LeaderboardSelector.get_leaderboards()
        return Response({"success": True, "data": LeaderboardSerializer(lbs, many=True).data})

class LeaderboardDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: LeaderboardSerializer})
    def get(self, request, pk):
        lb = LeaderboardSelector.get_leaderboard(pk)
        if not lb: return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": LeaderboardSerializer(lb).data})

class LeaderboardEntriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: LeaderboardEntrySerializer(many=True)})
    def get(self, request, pk):
        entries = LeaderboardSelector.get_top_entries(pk)
        return Response({"success": True, "data": LeaderboardEntrySerializer(entries, many=True).data})

# --- Rankings ---
class RankingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerRatingSerializer})
    def get(self, request):
        game_id = request.query_params.get('game_id')
        if not game_id:
            return Response({"success": False, "message": "game_id required"}, status=status.HTTP_400_BAD_REQUEST)
        rating = RankingSelector.get_player_rating(request.user, game_id)
        if not rating: return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": PlayerRatingSerializer(rating).data})

# --- Seasons ---
class SeasonListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: SeasonSerializer(many=True)})
    def get(self, request):
        seasons = SeasonSelector.get_seasons()
        return Response({"success": True, "data": SeasonSerializer(seasons, many=True).data})

class SeasonCurrentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: SeasonSerializer})
    def get(self, request):
        season = SeasonSelector.get_current_season()
        if not season: return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": SeasonSerializer(season).data})

# --- Events ---
class EventListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: LiveEventSerializer(many=True)})
    def get(self, request):
        events = EventSelector.get_active_events()
        return Response({"success": True, "data": LiveEventSerializer(events, many=True).data})

# --- Tournaments ---
class TournamentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: TournamentSerializer(many=True)})
    def get(self, request):
        tournaments = TournamentSelector.get_tournaments()
        return Response({"success": True, "data": TournamentSerializer(tournaments, many=True).data})

class TournamentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: TournamentSerializer})
    def get(self, request, pk):
        t = TournamentSelector.get_tournament(pk)
        if not t: return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": TournamentSerializer(t).data})

class TournamentRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=TournamentRegisterRequestSerializer, responses={200: dict})
    def post(self, request, pk):
        success, msg = TournamentService.register(request.user, pk)
        return Response(
            {"success": success, "message": msg}, 
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        )

class TournamentBracketView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: TournamentMatchSerializer(many=True)})
    def get(self, request, pk):
        bracket = TournamentSelector.get_bracket(pk)
        return Response({"success": True, "data": TournamentMatchSerializer(bracket, many=True).data})

# --- Statistics ---
class CompetitiveStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CompetitiveStatisticsSerializer})
    def get(self, request):
        stats = StatisticsSelector.get_statistics(request.user)
        if not stats: return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": CompetitiveStatisticsSerializer(stats).data})

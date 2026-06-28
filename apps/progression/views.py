from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .serializers import (
    PlayerProgressSerializer, PlayerAchievementSerializer, PlayerChallengeSerializer,
    PlayerStatisticsSerializer, PlayerBadgeSerializer, PlayerTitleSerializer
)
from .selectors import ProgressSelector, AchievementSelector, ChallengeSelector, StatisticsSelector, BadgeTitleSelector
# from .services import ChallengeService

class ProgressionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerProgressSerializer})
    def get(self, request):
        progress = ProgressSelector.get_progress(request.user)
        if not progress:
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": PlayerProgressSerializer(progress).data})

class StatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerStatisticsSerializer})
    def get(self, request):
        stats = StatisticsSelector.get_statistics(request.user)
        if not stats:
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": PlayerStatisticsSerializer(stats).data})

class AchievementsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerAchievementSerializer(many=True)})
    def get(self, request):
        achievements = AchievementSelector.get_player_achievements(request.user)
        return Response({"success": True, "data": PlayerAchievementSerializer(achievements, many=True).data})

class ChallengesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerChallengeSerializer(many=True)})
    def get(self, request):
        challenges = ChallengeSelector.get_player_challenges(request.user)
        return Response({"success": True, "data": PlayerChallengeSerializer(challenges, many=True).data})

class BadgesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerBadgeSerializer(many=True)})
    def get(self, request):
        badges = BadgeTitleSelector.get_badges(request.user)
        return Response({"success": True, "data": PlayerBadgeSerializer(badges, many=True).data})

class TitlesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PlayerTitleSerializer(many=True)})
    def get(self, request):
        titles = BadgeTitleSelector.get_titles(request.user)
        return Response({"success": True, "data": PlayerTitleSerializer(titles, many=True).data})

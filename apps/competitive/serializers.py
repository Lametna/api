from rest_framework import serializers
from .models import (
    Season, RankTier, PlayerRating, Leaderboard, LeaderboardEntry, 
    LiveEvent, Tournament, TournamentParticipant, TournamentMatch, CompetitiveStatistics
)

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ['id', 'name', 'description', 'start_time', 'end_time', 'is_active', 'metadata']

class RankTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = RankTier
        fields = ['id', 'name', 'min_rating', 'max_rating', 'icon_url']

class PlayerRatingSerializer(serializers.ModelSerializer):
    tier = RankTierSerializer(read_only=True)
    
    class Meta:
        model = PlayerRating
        fields = ['id', 'game_id', 'current_rating', 'peak_rating', 'tier']

class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = ['id', 'name', 'leaderboard_type', 'game_id', 'metadata']

class LeaderboardEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderboardEntry
        fields = ['id', 'user_id', 'score', 'rank_position']

class LiveEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveEvent
        fields = ['id', 'name', 'description', 'start_time', 'end_time', 'modifiers']

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'game_id', 'start_time', 'max_participants', 'status', 'rewards']

class TournamentParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentParticipant
        fields = ['id', 'user_id', 'registered_at']

class TournamentMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentMatch
        fields = ['id', 'round_number', 'parent_match', 'participant1', 'participant2', 'winner', 'match_ref_id']

class CompetitiveStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitiveStatistics
        fields = ['season_wins', 'season_losses', 'tournament_wins', 'tournament_matches']

class TournamentRegisterRequestSerializer(serializers.Serializer):
    tournament_id = serializers.UUIDField()

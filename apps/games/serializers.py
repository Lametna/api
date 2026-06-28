from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Game, Match, MatchPlayer, Score

User = get_user_model()

class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar']

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'plugin_id', 'name', 'description', 'version', 'developer', 'min_players', 'max_players', 'estimated_duration_mins', 'difficulty']

class MatchPlayerSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer(read_only=True)

    class Meta:
        model = MatchPlayer
        fields = ['id', 'user', 'status', 'team_id', 'joined_at']

class MatchSerializer(serializers.ModelSerializer):
    players = MatchPlayerSerializer(many=True, read_only=True)
    game = GameSerializer(read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'game', 'party', 'state', 'configuration', 'started_at', 'ended_at', 'players']

class ScoreSerializer(serializers.ModelSerializer):
    player = MatchPlayerSerializer(read_only=True)
    
    class Meta:
        model = Score
        fields = ['id', 'player', 'value', 'reason']

class MatchCreateSerializer(serializers.Serializer):
    game_id = serializers.UUIDField()
    party_id = serializers.UUIDField(required=False, allow_null=True)
    configuration = serializers.JSONField(required=False, default=dict)

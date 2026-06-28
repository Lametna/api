from django.utils import timezone
from typing import Dict, Any, Optional

from .models import Game, Match, MatchPlayer, Round, Turn, Score, GameResult
from apps.party.models import Party
from django.contrib.auth import get_user_model

User = get_user_model()

class GameRepository:
    @staticmethod
    def register_game(plugin_id: str, name: str, **kwargs) -> Game:
        game, created = Game.objects.update_or_create(
            plugin_id=plugin_id,
            defaults={'name': name, **kwargs}
        )
        return game

class MatchRepository:
    @staticmethod
    def create_match(game: Game, party: Optional[Party], config: Dict[str, Any]) -> Match:
        return Match.objects.create(game=game, party=party, configuration=config)

    @staticmethod
    def update_state(match: Match, new_state: str) -> Match:
        match.state = new_state
        if new_state == Match.State.RUNNING and not match.started_at:
            match.started_at = timezone.now()
        elif new_state in [Match.State.FINISHED, Match.State.CANCELLED]:
            match.ended_at = timezone.now()
        match.save(update_fields=['state', 'started_at', 'ended_at'])
        return match

    @staticmethod
    def add_player(match: Match, user: User, status: str = MatchPlayer.Status.ACTIVE) -> MatchPlayer:
        return MatchPlayer.objects.create(match=match, user=user, status=status)

class RoundRepository:
    @staticmethod
    def create_round(match: Match, round_number: int) -> Round:
        return Round.objects.create(match=match, round_number=round_number, started_at=timezone.now())

    @staticmethod
    def finish_round(round_obj: Round) -> Round:
        round_obj.ended_at = timezone.now()
        round_obj.save(update_fields=['ended_at'])
        return round_obj

class TurnRepository:
    @staticmethod
    def create_turn(round_obj: Round, player: MatchPlayer, turn_number: int) -> Turn:
        return Turn.objects.create(round=round_obj, player=player, turn_number=turn_number, started_at=timezone.now())

    @staticmethod
    def finish_turn(turn: Turn) -> Turn:
        turn.ended_at = timezone.now()
        turn.save(update_fields=['ended_at'])
        return turn

class ScoreRepository:
    @staticmethod
    def update_score(match: Match, player: MatchPlayer, value: int, reason: str = "") -> Score:
        score, created = Score.objects.get_or_create(match=match, player=player)
        score.value += value
        score.reason = reason
        score.save()
        return score

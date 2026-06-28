from typing import Optional, List
from .models import Game, Match, MatchPlayer, Round, Turn, Score

class GameSelector:
    @staticmethod
    def get_active_games() -> List[Game]:
        return list(Game.objects.filter(is_active=True))

    @staticmethod
    def get_game(game_id: str) -> Optional[Game]:
        return Game.objects.filter(id=game_id).first()

class MatchSelector:
    @staticmethod
    def get_match(match_id: str) -> Optional[Match]:
        return Match.objects.filter(id=match_id).first()

    @staticmethod
    def get_players(match: Match) -> List[MatchPlayer]:
        return list(MatchPlayer.objects.filter(match=match).select_related('user'))

    @staticmethod
    def get_player(match: Match, user_id: str) -> Optional[MatchPlayer]:
        return MatchPlayer.objects.filter(match=match, user_id=user_id).first()

class RoundSelector:
    @staticmethod
    def get_current_round(match: Match) -> Optional[Round]:
        return Round.objects.filter(match=match, ended_at__isnull=True).order_by('-round_number').first()

class TurnSelector:
    @staticmethod
    def get_current_turn(round_obj: Round) -> Optional[Turn]:
        return Turn.objects.filter(round=round_obj, ended_at__isnull=True).order_by('-turn_number').first()

class ScoreSelector:
    @staticmethod
    def get_scores(match: Match) -> List[Score]:
        return list(Score.objects.filter(match=match).select_related('player__user').order_by('-value'))

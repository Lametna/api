import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretWord
from .events import (
    WordAssignedEvent, ForbiddenWordUsedEvent, TabooWordSolvedEvent, TurnEndedEvent
)

class TabooPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.taboo"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Taboo",
            "category": "WORD",
            "min_players": 4,
            "max_players": 12,
            "has_turns": True,
            "configurable": ["rounds", "team_mode", "packs", "categories", "turn_timer"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        rounds = config.get("rounds", 3)
        return isinstance(rounds, int) and rounds > 0

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        if len(players) < 4: return
        
        teams = {"team_1": players[0::2], "team_2": players[1::2]}
        state = {
            "players": players,
            "teams": teams,
            "scores": {"team_1": 0, "team_2": 0},
            "current_team_turn": "team_1",
            "actor_idx": {"team_1": 0, "team_2": 0},
            "current_word_obj": None,
            "turn_score": 0
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        self._start_turn(match_id)

    def _start_turn(self, match_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        state["current_team_turn"] = "team_2" if state["current_team_turn"] == "team_1" else "team_1"
        team = state["current_team_turn"]
        state["actor_idx"][team] = (state["actor_idx"][team] + 1) % len(state["teams"][team])
        actor = state["teams"][team][state["actor_idx"][team]]
        state["turn_score"] = 0
        
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        self._next_word(match_id, actor)

    def _next_word(self, match_id: str, actor: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        from apps.games.services import DictionaryService
        
        word_obj = DictionaryService.get_weighted_random_word()
        
        if word_obj:
            word = word_obj.english_name
            # Extract forbidden words from tags
            tags = word_obj.tags if isinstance(word_obj.tags, list) else []
            forbidden = tags[:5] if tags else ["No", "Forbidden", "Words", "Defined", "Yet"]
            
            EventDispatcher.publish(WordAssignedEvent(
                match_id=match_id, actor_id=actor, word=word, forbidden_words=forbidden
            ))

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        team = state["current_team_turn"]
        actor = state["teams"][team][state["actor_idx"][team]]
        
        if action.get("type") == "MARK_SOLVED":
            # The actor marks it solved
            if player_id != actor: return False
            state["scores"][team] += 1
            state["turn_score"] += 1
            EventDispatcher.publish(TabooWordSolvedEvent(match_id=match_id, guesser_id="team", score_awarded=1))
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            self._next_word(match_id, actor)
            return True
            
        elif action.get("type") == "TABOO_BUZZER":
            # Someone from opposing team buzzed
            if player_id in state["teams"][team]: return False
            state["scores"][team] -= 1
            state["turn_score"] -= 1
            EventDispatcher.publish(ForbiddenWordUsedEvent(match_id=match_id, actor_id=actor))
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            self._next_word(match_id, actor)
            return True
            
        elif action.get("type") == "SKIP_WORD":
            if player_id != actor: return False
            self._next_word(match_id, actor)
            return True
            
        elif action.get("type") == "END_TURN":
            # Timer ended
            EventDispatcher.publish(TurnEndedEvent(match_id=match_id, actor_id=actor, score_delta=state["turn_score"]))
            self._start_turn(match_id)
            return True
            
        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        max_score = max(state["scores"].values(), default=0)
        winning_teams = [t for t, s in state["scores"].items() if s == max_score]
        
        winners = []
        for t in winning_teams:
            winners.extend(state["teams"][t])
        return winners

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

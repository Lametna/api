import random
import time
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretWord
from .events import (
    SecretWordAssignedEvent, ClueSubmittedEvent, PasswordGuessSubmittedEvent, WordSolvedEvent
)

class PasswordPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.password"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Password",
            "category": "WORD",
            "min_players": 4,
            "max_players": 12,
            "has_turns": True,
            "configurable": ["rounds", "team_mode", "packs", "categories", "round_timer"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        rounds = config.get("rounds", 3)
        return isinstance(rounds, int) and rounds > 0

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        if len(players) < 4: return
        
        # Simple MVP Team assignment: Evens vs Odds
        teams = {"team_1": players[0::2], "team_2": players[1::2]}
        
        state = {
            "players": players,
            "teams": teams,
            "scores": {"team_1": 0, "team_2": 0},
            "current_team_turn": "team_1",
            "clue_giver_idx": {"team_1": 0, "team_2": 0},
            "current_word": None,
            "phase": "WAIT_FOR_CLUE" # WAIT_FOR_CLUE, WAIT_FOR_GUESS
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        self._next_turn(match_id)

    def _next_turn(self, match_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        # Toggle team
        state["current_team_turn"] = "team_2" if state["current_team_turn"] == "team_1" else "team_1"
        team = state["current_team_turn"]
        
        # Advance clue giver
        state["clue_giver_idx"][team] = (state["clue_giver_idx"][team] + 1) % len(state["teams"][team])
        giver = state["teams"][team][state["clue_giver_idx"][team]]
        
        from apps.games.services import DictionaryService
        
        word_obj = DictionaryService.get_weighted_random_word()
        state["current_word"] = word_obj.english_name.lower() if word_obj else "password"
        state["phase"] = "WAIT_FOR_CLUE"
        
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        EventDispatcher.publish(SecretWordAssignedEvent(
            match_id=match_id, team_id=team, clue_giver_id=giver
        ))

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        team = state["current_team_turn"]
        giver = state["teams"][team][state["clue_giver_idx"][team]]
        
        if action.get("type") == "SUBMIT_CLUE" and state["phase"] == "WAIT_FOR_CLUE":
            if player_id != giver: return False
            clue = action.get("clue", "").strip()
            
            # Simple validation: one word, not the secret
            if " " in clue or clue.lower() in state["current_word"]: return False
            
            state["phase"] = "WAIT_FOR_GUESS"
            EventDispatcher.publish(ClueSubmittedEvent(match_id=match_id, clue_giver_id=player_id, clue=clue))
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "SUBMIT_GUESS" and state["phase"] == "WAIT_FOR_GUESS":
            # Must be someone on the same team, not the giver
            if player_id not in state["teams"][team] or player_id == giver: return False
            
            guess = action.get("guess", "").lower().strip()
            EventDispatcher.publish(PasswordGuessSubmittedEvent(match_id=match_id, guesser_id=player_id, guess=guess))
            
            if guess == state["current_word"]:
                state["scores"][team] += 10
                EventDispatcher.publish(WordSolvedEvent(match_id=match_id, team_id=team, score_awarded=10))
            
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            self._next_turn(match_id)
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

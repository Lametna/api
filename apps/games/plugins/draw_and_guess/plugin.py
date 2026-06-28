import random
import time
from typing import Dict, Any, List
from django.core.cache import cache
from django.db.models import Q
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretWord
from .events import (
    DrawingStartedEvent, GuessSubmittedEvent, CorrectGuessEvent, RoundFinishedEvent
)

class DrawAndGuessPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.draw_and_guess"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Draw & Guess",
            "category": "DRAWING",
            "min_players": 2,
            "max_players": 12,
            "has_turns": True,
            "configurable": ["rounds", "drawing_timer", "difficulty", "packs", "categories"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        rounds = config.get("rounds", 3)
        return isinstance(rounds, int) and rounds > 0

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "current_drawer_idx": -1,
            "current_word": None,
            "guessed_players": [],
            "round_start_time": 0
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        state["current_drawer_idx"] = (state["current_drawer_idx"] + 1) % len(state["players"])
        drawer = state["players"][state["current_drawer_idx"]]
        state["guessed_players"] = []
        
        from apps.games.services import DictionaryService
        
        word_obj = DictionaryService.get_weighted_random_word()
        if word_obj:
            state["current_word"] = word_obj.english_name.lower()
        else:
            state["current_word"] = "apple" # fallback
            
        state["round_start_time"] = time.time()
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        EventDispatcher.publish(DrawingStartedEvent(match_id=match_id, drawer_id=drawer, round_number=1))

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        if action.get("type") == "SUBMIT_GUESS":
            guess = action.get("guess", "").lower().strip()
            EventDispatcher.publish(GuessSubmittedEvent(match_id=match_id, player_id=player_id, guess=guess))
            
            drawer = state["players"][state["current_drawer_idx"]]
            if player_id == drawer or player_id in state["guessed_players"]:
                return False
                
            if guess == state["current_word"]:
                state["guessed_players"].append(player_id)
                # Score based on speed
                time_taken = time.time() - state["round_start_time"]
                score = max(10, int(100 - time_taken))
                state["scores"][player_id] += score
                
                # Drawer also gets points
                state["scores"][drawer] += 10
                
                EventDispatcher.publish(CorrectGuessEvent(match_id=match_id, player_id=player_id, score_awarded=score))
                
                # Check if everyone guessed
                if len(state["guessed_players"]) >= len(state["players"]) - 1:
                    EventDispatcher.publish(RoundFinishedEvent(match_id=match_id, secret_word=state["current_word"]))
                
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True
                
        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        max_score = max(state["scores"].values(), default=0)
        return [p for p, s in state["scores"].items() if s == max_score]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

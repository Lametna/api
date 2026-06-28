import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import GuessSubmittedEvent, NumberFoundEvent

class NumberGuessingPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.number_guessing"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Number Guessing",
            "category": "PUZZLE",
            "min_players": 1,
            "max_players": 8,
            "has_turns": False
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        max_num = config.get("max_number", 100)
        return isinstance(max_num, int) and max_num > 1

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        # We fetch config from match (abstracted out for simplicity, assuming 100 here)
        target_number = random.randint(1, 100)
        state = {
            "target": target_number,
            "winners": [],
            "attempts": {p: 0 for p in players}
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass # Only 1 round

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        if action.get("type") != "SUBMIT_GUESS":
            return False
            
        guess = action.get("value")
        if not isinstance(guess, int): return False
        
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        state["attempts"][player_id] += 1
        EventDispatcher.publish(GuessSubmittedEvent(match_id=match_id, player_id=player_id, guess=guess))
        
        if guess == state["target"] and player_id not in state["winners"]:
            state["winners"].append(player_id)
            EventDispatcher.publish(NumberFoundEvent(
                match_id=match_id, player_id=player_id, 
                number=state["target"], attempts=state["attempts"][player_id]
            ))
            
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        return True

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        
        if len(state["winners"]) > 0:
            return state["winners"]
        return []

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

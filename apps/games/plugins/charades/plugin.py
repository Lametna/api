import random
import time
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretWord
from .events import PromptAssignedEvent, RoundStartedEvent, PromptSolvedEvent

class CharadesPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.charades"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Charades",
            "category": "ACTING",
            "min_players": 2,
            "max_players": 20,
            "has_turns": True,
            "configurable": ["rounds", "acting_timer", "team_mode", "packs", "categories", "skips_allowed"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        rounds = config.get("rounds", 3)
        return isinstance(rounds, int) and rounds > 0

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "current_actor_idx": -1,
            "current_word": None,
            "turn_start_time": 0
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        EventDispatcher.publish(RoundStartedEvent(match_id=match_id, round_number=1))
        self._next_turn(match_id)

    def _next_turn(self, match_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        state["current_actor_idx"] = (state["current_actor_idx"] + 1) % len(state["players"])
        actor = state["players"][state["current_actor_idx"]]
        
        from apps.games.services import DictionaryService
        
        word_obj = DictionaryService.get_weighted_random_word()
        state["current_word"] = word_obj.english_name.lower() if word_obj else "movie"
        
        state["turn_start_time"] = time.time()
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        EventDispatcher.publish(PromptAssignedEvent(
            match_id=match_id, actor_id=actor, prompt_id=str(word_obj.id) if word_obj else "1"
        ))

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        if action.get("type") == "MARK_SOLVED":
            # The host or the actor indicates someone solved it
            guesser = action.get("guesser_id")
            if not guesser or guesser == state["players"][state["current_actor_idx"]]: return False
            
            time_taken = int(time.time() - state["turn_start_time"])
            score = max(10, 100 - time_taken)
            
            state["scores"][guesser] += score
            state["scores"][state["players"][state["current_actor_idx"]]] += score // 2
            
            EventDispatcher.publish(PromptSolvedEvent(match_id=match_id, guesser_id=guesser, time_taken_secs=time_taken))
            
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            self._next_turn(match_id)
            return True
            
        elif action.get("type") == "SKIP_PROMPT":
            self._next_turn(match_id)
            return True
            
        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        max_score = max(state["scores"].values(), default=0)
        return [p for p, s in state["scores"].items() if s == max_score]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

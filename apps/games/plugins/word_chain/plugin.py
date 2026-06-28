import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import WordSubmittedEvent, TurnExpiredEvent, PlayerEliminatedEvent

class WordChainPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.word_chain"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Word Chain",
            "category": "WORD",
            "min_players": 2,
            "max_players": 12,
            "has_turns": True,
            "configurable": ["language", "turn_timer", "elimination_mode"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        state = {
            "players": players,
            "alive": players.copy(),
            "scores": {p: 0 for p in players},
            "used_words": set(),
            "last_letter": None,
            "current_turn_idx": 0,
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def _next_turn(self, state, match_id):
        if len(state["alive"]) <= 1:
            state["winner"] = True
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return
            
        state["current_turn_idx"] = (state["current_turn_idx"] + 1) % len(state["players"])
        while state["players"][state["current_turn_idx"]] not in state["alive"]:
            state["current_turn_idx"] = (state["current_turn_idx"] + 1) % len(state["players"])

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state or state["winner"] or player_id not in state["alive"]: return False
        
        current_player = state["players"][state["current_turn_idx"]]
        
        if action.get("type") == "SUBMIT_WORD":
            if player_id != current_player: return False
            
            word = action.get("word", "").lower().strip()
            if not word or word in state["used_words"]: return False
            
            if state["last_letter"] and not word.startswith(state["last_letter"]):
                return False
                
            state["used_words"].add(word)
            state["last_letter"] = word[-1]
            state["scores"][player_id] += len(word)
            
            EventDispatcher.publish(WordSubmittedEvent(
                match_id=match_id, player_id=player_id, word=word, score_awarded=len(word)
            ))
            
            self._next_turn(state, match_id)
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "TURN_EXPIRED":
            if player_id != current_player: return False
            EventDispatcher.publish(TurnExpiredEvent(match_id=match_id, player_id=player_id))
            
            state["alive"].remove(player_id)
            EventDispatcher.publish(PlayerEliminatedEvent(match_id=match_id, player_id=player_id))
            
            state["last_letter"] = None # Reset chain
            self._next_turn(state, match_id)
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True

        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner"]: return []
        if len(state["alive"]) == 1:
            return state["alive"]
        max_score = max(state["scores"].values(), default=0)
        return [p for p, s in state["scores"].items() if s == max_score]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import CardFlippedEvent, PairMatchedEvent, TurnEndedEvent, GameFinishedEvent

class MemoryMatchPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.memory_match"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Memory Match",
            "category": "PUZZLE",
            "min_players": 1,
            "max_players": 4,
            "has_turns": True,
            "configurable": ["grid_size"] # e.g. "4x4", "6x6"
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        grid_size = 16 # MVP: 4x4
        values = [str(i) for i in range(grid_size // 2)] * 2
        random.shuffle(values)
        
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "grid": values,
            "matched_indices": set(),
            "current_turn_idx": 0,
            "flipped_indices": [],
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state or state["winner"]: return False
        
        current_player = state["players"][state["current_turn_idx"]]
        if player_id != current_player: return False
        
        if action.get("type") == "FLIP_CARD":
            idx = action.get("card_index")
            if not isinstance(idx, int) or idx < 0 or idx >= len(state["grid"]): return False
            if idx in state["matched_indices"] or idx in state["flipped_indices"]: return False
            
            state["flipped_indices"].append(idx)
            val = state["grid"][idx]
            EventDispatcher.publish(CardFlippedEvent(match_id=match_id, player_id=player_id, card_index=idx, card_value=val))
            
            if len(state["flipped_indices"]) == 2:
                idx1, idx2 = state["flipped_indices"]
                if state["grid"][idx1] == state["grid"][idx2]:
                    # Match
                    state["matched_indices"].add(idx1)
                    state["matched_indices"].add(idx2)
                    state["scores"][player_id] += 10
                    EventDispatcher.publish(PairMatchedEvent(
                        match_id=match_id, player_id=player_id, 
                        card_index_1=idx1, card_index_2=idx2, score_awarded=10
                    ))
                    # Player gets to go again, don't advance turn_idx
                else:
                    # No match, advance turn
                    state["current_turn_idx"] = (state["current_turn_idx"] + 1) % len(state["players"])
                    EventDispatcher.publish(TurnEndedEvent(match_id=match_id, player_id=player_id))
                    
                state["flipped_indices"] = []
                
            # Check win condition
            if len(state["matched_indices"]) == len(state["grid"]):
                state["winner"] = True
                max_score = max(state["scores"].values(), default=0)
                winners = [p for p, s in state["scores"].items() if s == max_score]
                EventDispatcher.publish(GameFinishedEvent(match_id=match_id, winners=winners))
                
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner"]: return []
        max_score = max(state["scores"].values(), default=0)
        return [p for p, s in state["scores"].items() if s == max_score]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

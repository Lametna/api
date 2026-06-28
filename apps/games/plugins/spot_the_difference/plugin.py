import math
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import DifferenceFoundEvent, HintUsedEvent, RoundFinishedEvent

class SpotTheDifferencePlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.spot_the_difference"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Spot the Difference",
            "category": "PUZZLE",
            "min_players": 1,
            "max_players": 8,
            "has_turns": False,
            "configurable": ["rounds", "difficulty", "hints_allowed"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        # Mock dataset of differences. X, Y, Radius
        mock_differences = {
            "diff_1": {"x": 150, "y": 300, "r": 20},
            "diff_2": {"x": 450, "y": 100, "r": 15},
            "diff_3": {"x": 200, "y": 500, "r": 25}
        }
        
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "differences": mock_differences,
            "found_by_player": {p: set() for p in players},
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state or state["winner"]: return False
        
        if action.get("type") == "CLICK_COORDINATE":
            x = action.get("x")
            y = action.get("y")
            if x is None or y is None: return False
            
            # Validation
            found_id = None
            for diff_id, bounds in state["differences"].items():
                if diff_id in state["found_by_player"][player_id]: continue
                
                dist = math.hypot(x - bounds["x"], y - bounds["y"])
                if dist <= bounds["r"]:
                    found_id = diff_id
                    break
                    
            if found_id:
                state["found_by_player"][player_id].add(found_id)
                state["scores"][player_id] += 10
                EventDispatcher.publish(DifferenceFoundEvent(
                    match_id=match_id, player_id=player_id, 
                    difference_id=found_id, score_awarded=10
                ))
                
                # Check if this player found all
                if len(state["found_by_player"][player_id]) == len(state["differences"]):
                    state["winner"] = True
                    EventDispatcher.publish(RoundFinishedEvent(match_id=match_id, leaderboard=state["scores"]))
                    
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True
                
        elif action.get("type") == "USE_HINT":
            EventDispatcher.publish(HintUsedEvent(match_id=match_id, player_id=player_id))
            return True

        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner"]: return []
        max_score = max(state["scores"].values(), default=0)
        return [p for p, s in state["scores"].items() if s == max_score]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

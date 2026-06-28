import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import BingoMarkedEvent, BingoCompletedEvent

class BingoPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.bingo"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Bingo",
            "category": "BOARD",
            "min_players": 2,
            "max_players": 100,
            "has_turns": False
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        max_num = config.get("max_number", 75)
        return isinstance(max_num, int) and max_num >= 25

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        # Generate cards
        cards = {}
        for player in players:
            nums = random.sample(range(1, 76), 25)
            # 5x5 grid
            card = [nums[i:i+5] for i in range(0, 25, 5)]
            card[2][2] = 0 # Free space
            cards[player] = card
            
        state = {
            "players": players,
            "cards": cards,
            "marks": {p: [[False]*5 for _ in range(5)] for p in players},
            "drawn_numbers": [],
            "winners": []
        }
        
        # Mark free space
        for p in players:
            state["marks"][p][2][2] = True
            
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        if action.get("type") == "DRAW_NUMBER":
            # Admin action
            available = [n for n in range(1, 76) if n not in state["drawn_numbers"]]
            if not available: return False
            num = random.choice(available)
            state["drawn_numbers"].append(num)
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "MARK_NUMBER":
            number = action.get("value")
            if number not in state["drawn_numbers"]: return False
            
            card = state["cards"][player_id]
            marks = state["marks"][player_id]
            
            for r in range(5):
                for c in range(5):
                    if card[r][c] == number:
                        marks[r][c] = True
                        EventDispatcher.publish(BingoMarkedEvent(
                            match_id=match_id, player_id=player_id, number=number, row=r, col=c
                        ))
                        
                        # Check win (MVP: any full row/col/diag = win)
                        if self._check_win(marks):
                            if player_id not in state["winners"]:
                                state["winners"].append(player_id)
                                EventDispatcher.publish(BingoCompletedEvent(
                                    match_id=match_id, player_id=player_id, lines_completed=1
                                ))
                        break
                        
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        return False

    def _check_win(self, marks: List[List[bool]]) -> bool:
        # Check rows & cols
        for i in range(5):
            if all(marks[i]): return True
            if all(marks[r][i] for r in range(5)): return True
        # Check diagonals
        if all(marks[i][i] for i in range(5)): return True
        if all(marks[i][4-i] for i in range(5)): return True
        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        return state["winners"]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

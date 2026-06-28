import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretCategory
from .events import CategoryGeneratedEvent, AnswerSubmittedEvent, AnswersLockedEvent, RoundScoredEvent

class CategoriesPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.categories"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Categories",
            "category": "WORD",
            "min_players": 2,
            "max_players": 12,
            "has_turns": False,
            "configurable": ["rounds", "round_timer", "packs"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "current_round": 0,
            "rounds_data": {},
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        state["current_round"] += 1
        
        cats = list(SecretCategory.objects.filter(is_active=True))
        cat_name = random.choice(cats).name if cats else "Colors"
        
        state["rounds_data"][state["current_round"]] = {
            "category": cat_name,
            "answers": {p: set() for p in state["players"]},
            "phase": "RUNNING"
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        EventDispatcher.publish(CategoryGeneratedEvent(
            match_id=match_id, round_number=state["current_round"], category_name=cat_name
        ))

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        r_num = state["current_round"]
        round_data = state["rounds_data"].get(r_num)
        if not round_data: return False
        
        if action.get("type") == "SUBMIT_ANSWER" and round_data["phase"] == "RUNNING":
            ans = action.get("answer", "").strip().lower()
            if ans:
                round_data["answers"][player_id].add(ans)
                EventDispatcher.publish(AnswerSubmittedEvent(match_id=match_id, player_id=player_id))
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True
                
        elif action.get("type") == "LOCK_ANSWERS" and round_data["phase"] == "RUNNING":
            round_data["phase"] = "SCORING"
            EventDispatcher.publish(AnswersLockedEvent(match_id=match_id))
            
            # Simple deduplication scoring MVP
            all_answers = {}
            for p, p_answers in round_data["answers"].items():
                for a in p_answers:
                    all_answers[a] = all_answers.get(a, 0) + 1
                    
            for p, p_answers in round_data["answers"].items():
                for a in p_answers:
                    if all_answers[a] == 1:
                        state["scores"][p] += 10 # Unique points
                        
            EventDispatcher.publish(RoundScoredEvent(match_id=match_id, leaderboard=state["scores"]))
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True

        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state.get("winner"): return []
        max_score = max(state["scores"].values(), default=0)
        return [p for p, s in state["scores"].items() if s == max_score]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

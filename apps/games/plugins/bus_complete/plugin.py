import random
import string
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretCategory
from .events import (
    LetterGeneratedEvent, AnswerSubmittedEvent, AnswersLockedEvent,
    AnswerValidatedEvent, RoundScoredEvent, BusCompletedEvent
)

class BusCompletePlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.bus_complete"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Bus Complete",
            "category": "WORD",
            "min_players": 2,
            "max_players": 12,
            "has_turns": False,
            "configurable": ["language", "rounds", "round_timer", "categories", "random_letter"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        rounds = config.get("rounds", 3)
        return isinstance(rounds, int) and rounds > 0

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        # Resolve categories. Mocking selection for MVP:
        cats = list(SecretCategory.objects.filter(is_active=True)[:5])
        if not cats:
            cat_names = ["Boy", "Girl", "Animal", "Plant", "Inanimate"]
        else:
            cat_names = [c.name for c in cats]
            
        state = {
            "players": players,
            "categories": cat_names,
            "current_round": 0,
            "rounds_data": {},
            "scores": {p: 0 for p in players},
            "phase": "WAITING" # WAITING, RUNNING, VALIDATING
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        state["current_round"] += 1
        letter = random.choice(string.ascii_uppercase)
        
        state["phase"] = "RUNNING"
        state["rounds_data"][state["current_round"]] = {
            "letter": letter,
            "answers": {p: {c: "" for c in state["categories"]} for p in state["players"]},
            "validated": {p: {c: False for c in state["categories"]} for p in state["players"]}
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        EventDispatcher.publish(LetterGeneratedEvent(match_id=match_id, round_number=state["current_round"], letter=letter))

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        r_num = state["current_round"]
        round_data = state["rounds_data"].get(r_num)
        if not round_data: return False
        
        if action.get("type") == "SUBMIT_ANSWER" and state["phase"] == "RUNNING":
            cat = action.get("category")
            ans = action.get("answer", "").strip().upper()
            if cat in state["categories"]:
                round_data["answers"][player_id][cat] = ans
                EventDispatcher.publish(AnswerSubmittedEvent(match_id=match_id, player_id=player_id, category=cat))
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True
                
        elif action.get("type") == "LOCK_ANSWERS" and state["phase"] == "RUNNING":
            # Can be triggered by host or timer
            state["phase"] = "VALIDATING"
            EventDispatcher.publish(AnswersLockedEvent(match_id=match_id, round_number=r_num))
            
            # Auto-validator MVP: simply check if it starts with the correct letter
            letter = round_data["letter"]
            for p in state["players"]:
                for c in state["categories"]:
                    ans = round_data["answers"][p][c]
                    if ans.startswith(letter):
                        round_data["validated"][p][c] = True
            
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "HOST_VALIDATE" and state["phase"] == "VALIDATING":
            # Manual host overrides
            p_id = action.get("target_player")
            cat = action.get("category")
            is_valid = action.get("is_valid")
            if p_id in state["players"] and cat in state["categories"]:
                round_data["validated"][p_id][cat] = is_valid
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True
                
        elif action.get("type") == "FINISH_ROUND" and state["phase"] == "VALIDATING":
            # Score calculation
            for cat in state["categories"]:
                valid_answers = {}
                for p in state["players"]:
                    if round_data["validated"][p][cat]:
                        ans = round_data["answers"][p][cat]
                        valid_answers[ans] = valid_answers.get(ans, 0) + 1
                        
                for p in state["players"]:
                    if round_data["validated"][p][cat]:
                        ans = round_data["answers"][p][cat]
                        score = 10 if valid_answers[ans] == 1 else 5 # Unique = 10, shared = 5
                        state["scores"][p] += score
                        EventDispatcher.publish(AnswerValidatedEvent(match_id=match_id, player_id=p, category=cat, is_valid=True, score_awarded=score))
            
            state["phase"] = "WAITING"
            EventDispatcher.publish(RoundScoredEvent(match_id=match_id, round_number=r_num, leaderboard=state["scores"]))
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True

        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        # Return winners if Match Engine calls this after all rounds are complete.
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        
        # If the match engine determines it's over, find highest score
        max_score = max(state["scores"].values(), default=0)
        winners = [p for p, s in state["scores"].items() if s == max_score]
        
        if winners:
            EventDispatcher.publish(BusCompletedEvent(match_id=match_id, winners=winners))
            
        return winners

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

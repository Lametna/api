import random
import time
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import QuestionAnsweredEvent

QUESTIONS = [
    {"id": "q1", "text": "What is the capital of France?", "options": ["London", "Berlin", "Paris", "Madrid"], "correct_idx": 2},
    {"id": "q2", "text": "Which planet is known as the Red Planet?", "options": ["Earth", "Mars", "Jupiter", "Saturn"], "correct_idx": 1},
    {"id": "q3", "text": "Who wrote Hamlet?", "options": ["Dickens", "Shakespeare", "Hemingway", "Tolkien"], "correct_idx": 1},
    {"id": "q4", "text": "What is 2 + 2?", "options": ["3", "4", "5", "22"], "correct_idx": 1},
]

class TriviaPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.trivia"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Trivia",
            "category": "KNOWLEDGE",
            "min_players": 1,
            "max_players": 50,
            "has_turns": False
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        rounds = config.get("rounds", 3)
        return isinstance(rounds, int) and rounds > 0

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "current_question": None,
            "question_start_time": 0,
            "answers_this_round": {},
            "asked_questions": []
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        state = cache.get(f"match_state:{match_id}")
        if not state: return
        
        available = [q for q in QUESTIONS if q["id"] not in state["asked_questions"]]
        if not available:
            available = QUESTIONS # Reset if we run out for MVP
            
        q = random.choice(available)
        state["current_question"] = q
        state["asked_questions"].append(q["id"])
        state["question_start_time"] = time.time()
        state["answers_this_round"] = {}
        
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        if action.get("type") != "SUBMIT_ANSWER":
            return False
            
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["current_question"]: return False
        
        if player_id in state["answers_this_round"]: return False # Already answered
        
        answer_idx = action.get("value")
        if not isinstance(answer_idx, int): return False
        
        time_taken_ms = int((time.time() - state["question_start_time"]) * 1000)
        is_correct = (answer_idx == state["current_question"]["correct_idx"])
        
        state["answers_this_round"][player_id] = answer_idx
        
        if is_correct:
            # Score calculation: base + speed bonus
            score = 100 + max(0, 10000 - time_taken_ms) // 100
            state["scores"][player_id] += score
            
        EventDispatcher.publish(QuestionAnsweredEvent(
            match_id=match_id, player_id=player_id, 
            question_id=state["current_question"]["id"], 
            is_correct=is_correct, time_taken_ms=time_taken_ms
        ))
        
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        return True

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        # Trivia usually ends when all rounds are done, handled by Match Engine round counter.
        # When Match Engine signals end, it asks for winners.
        state = cache.get(f"match_state:{match_id}")
        if not state: return []
        
        # In a real scenario, this would only return winners IF the match is flagged as finished.
        # But per the SDK, if this returns non-empty, the match ends immediately.
        # So we return empty list to let MatchEngine handle the round loop.
        # For the sake of this mock, if scores > 500, win:
        winners = [p for p, s in state["scores"].items() if s >= 500]
        return winners

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.services import DictionaryService
from .events import LetterGuessedEvent, WordSolvedEvent, IncorrectGuessEvent

class HangmanPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.hangman"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Hangman",
            "category": "WORD",
            "min_players": 1,
            "max_players": 8,
            "has_turns": True,
            "configurable": ["max_strikes", "packs", "categories", "team_mode"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        word_obj = DictionaryService.get_weighted_random_word()
        word = word_obj.english_name.lower() if word_obj else "hangman"
        
        state = {
            "players": players,
            "scores": {p: 0 for p in players},
            "word": word,
            "guessed_letters": set(),
            "strikes": 0,
            "max_strikes": 6,
            "current_turn_idx": 0,
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state or state["winner"] or state["strikes"] >= state["max_strikes"]: return False
        
        current_player = state["players"][state["current_turn_idx"]]
        if player_id != current_player: return False
        
        if action.get("type") == "GUESS_LETTER":
            letter = action.get("letter", "").lower().strip()
            if not letter or len(letter) > 1 or letter in state["guessed_letters"]: return False
            
            state["guessed_letters"].add(letter)
            
            if letter in state["word"]:
                # Correct
                occurrences = state["word"].count(letter)
                state["scores"][player_id] += occurrences * 10
                EventDispatcher.publish(LetterGuessedEvent(
                    match_id=match_id, player_id=player_id, letter=letter, is_correct=True
                ))
                
                # Check win
                if all(c in state["guessed_letters"] for c in state["word"] if c.isalpha()):
                    state["winner"] = True
                    max_score = max(state["scores"].values(), default=0)
                    winners = [p for p, s in state["scores"].items() if s == max_score]
                    EventDispatcher.publish(WordSolvedEvent(match_id=match_id, winners=winners))
            else:
                # Incorrect
                state["strikes"] += 1
                EventDispatcher.publish(LetterGuessedEvent(
                    match_id=match_id, player_id=player_id, letter=letter, is_correct=False
                ))
                EventDispatcher.publish(IncorrectGuessEvent(match_id=match_id, strikes=state["strikes"]))
                
                if state["strikes"] >= state["max_strikes"]:
                    state["winner"] = True # Ended, technically a loss but we finish the match
                
            state["current_turn_idx"] = (state["current_turn_idx"] + 1) % len(state["players"])
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

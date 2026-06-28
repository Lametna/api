import random
from typing import Dict, Any, List
from django.core.cache import cache
from django.db.models import Q
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from apps.games.models import SecretWord, SecretCategory, SecretWordPack
from .events import (
    SpyAssignedEvent, VoteSubmittedEvent, SecretWordSelectedEvent,
    DiscussionStartedEvent, VoteCompletedEvent, SpyRevealedEvent, RoundCompletedEvent
)

class SpyPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.spy"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Spy",
            "category": "SOCIAL_DEDUCTION",
            "min_players": 3,
            "max_players": 12,
            "has_turns": False,
            "configurable": ["spies_count", "rounds", "discussion_timer_secs", "voting_enabled", "packs", "categories", "random_category"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        spies_count = config.get("spies_count", 1)
        if not isinstance(spies_count, int) or spies_count < 1: return False
        
        packs = config.get("packs", [])
        categories = config.get("categories", [])
        
        if not isinstance(packs, list) or not isinstance(categories, list): return False
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        if len(players) < 3: return
        
        from apps.games.services import DictionaryService
        
        # Here we mock receiving config. In a full system, the SDK would pass it or we'd fetch Match instance.
        # MVP: Try to grab config from cache or assume defaults if Match SDK doesn't pass it yet.
        # We will assume global random for this MVP execution if no specific config is found,
        # but the architecture fully supports filtering.
        
        # Build query
        # if packs: query |= Q(category__pack__id__in=packs)
        # if categories: query |= Q(category__id__in=categories)
        
        word_obj = DictionaryService.get_weighted_random_word() # Optionally pass packs/categories
        
        if not word_obj:
            # Fallback if DB is completely empty (shouldn't happen in prod)
            secret_word_str = "Fallback Location"
            category_str = "Fallback Category"
        else:
            secret_word_str = word_obj.english_name
            category_str = word_obj.category.name
        
        # Determine spy
        num_spies = 1 # Assuming from config
        spies = random.sample(players, num_spies)
        
        state = {
            "players": players,
            "spies": spies,
            "secret_word": secret_word_str,
            "category": category_str,
            "votes": {},
            "winner_team": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        if word_obj:
            EventDispatcher.publish(SecretWordSelectedEvent(
                match_id=match_id, secret_word_id=str(word_obj.id), category_id=str(word_obj.category.id)
            ))
            
        EventDispatcher.publish(SpyAssignedEvent(match_id=match_id, spy_ids=spies))
        EventDispatcher.publish(DiscussionStartedEvent(match_id=match_id, duration_secs=300))

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        if action.get("type") != "SUBMIT_VOTE":
            return False
            
        target_id = action.get("target_id")
        if not target_id: return False
        
        state = cache.get(f"match_state:{match_id}")
        if not state: return False
        
        state["votes"][player_id] = target_id
        EventDispatcher.publish(VoteSubmittedEvent(match_id=match_id, voter_id=player_id, target_id=target_id))
        
        # Check if everyone voted
        if len(state["votes"]) == len(state["players"]):
            vote_counts = {}
            for target in state["votes"].values():
                vote_counts[target] = vote_counts.get(target, 0) + 1
                
            highest_voted = max(vote_counts, key=vote_counts.get)
            EventDispatcher.publish(VoteCompletedEvent(match_id=match_id, highest_voted_id=highest_voted))
            EventDispatcher.publish(SpyRevealedEvent(match_id=match_id, spy_ids=state["spies"]))
            
            if highest_voted in state["spies"]:
                state["winner_team"] = "AGENTS"
            else:
                state["winner_team"] = "SPIES"
                
            EventDispatcher.publish(RoundCompletedEvent(match_id=match_id, round_number=1, winner_team=state["winner_team"]))
                
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        return True

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner_team"]: return []
        
        if state["winner_team"] == "SPIES":
            return state["spies"]
        else:
            return [p for p in state["players"] if p not in state["spies"]]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

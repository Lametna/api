import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import (
    RoleAssignedEvent, NightActionEvent, VoteCompletedEvent,
    PlayerEliminatedEvent, MatchFinishedEvent
)

class WerewolfPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.werewolf"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Werewolf",
            "category": "SOCIAL_DEDUCTION",
            "min_players": 5,
            "max_players": 20,
            "has_turns": False,
            "configurable": ["werewolf_count", "seer_enabled", "doctor_enabled"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        if len(players) < 5: return
        roles = ["WEREWOLF"] * 2 + ["DOCTOR", "SEER"] + ["VILLAGER"] * (len(players) - 4)
        random.shuffle(roles)
        
        player_roles = {p: roles[i] for i, p in enumerate(players)}
        state = {
            "players": players,
            "alive": players.copy(),
            "roles": player_roles,
            "phase": "NIGHT",
            "night_actions": {},
            "votes": {},
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        for p, r in player_roles.items():
            EventDispatcher.publish(RoleAssignedEvent(match_id=match_id, player_id=p, role=r))

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state or state["winner"] or player_id not in state["alive"]: return False
        
        if action.get("type") == "FORCE_TRANSITION":
            if state["phase"] == "NIGHT":
                killed = state["night_actions"].get("WEREWOLF")
                saved = state["night_actions"].get("DOCTOR")
                
                eliminated = killed if killed != saved else None
                if eliminated:
                    state["alive"].remove(eliminated)
                    EventDispatcher.publish(PlayerEliminatedEvent(match_id=match_id, player_id=eliminated, reason="WEREWOLF_KILLED"))
                    
                state["phase"] = "DAY"
            elif state["phase"] == "DAY":
                state["phase"] = "VOTING"
                state["votes"] = {}
            elif state["phase"] == "VOTING":
                if state["votes"]:
                    vote_counts = {}
                    for t in state["votes"].values():
                        vote_counts[t] = vote_counts.get(t, 0) + 1
                    highest = max(vote_counts, key=vote_counts.get)
                    state["alive"].remove(highest)
                    EventDispatcher.publish(VoteCompletedEvent(match_id=match_id, eliminated_id=highest))
                    EventDispatcher.publish(PlayerEliminatedEvent(match_id=match_id, player_id=highest, reason="LYNCHED"))
                
                state["phase"] = "NIGHT"
                state["night_actions"] = {}
                
            ww_count = sum(1 for p in state["alive"] if state["roles"][p] == "WEREWOLF")
            v_count = len(state["alive"]) - ww_count
            if ww_count == 0: state["winner"] = "VILLAGERS"
            elif ww_count >= v_count: state["winner"] = "WEREWOLVES"
            
            if state["winner"]:
                EventDispatcher.publish(MatchFinishedEvent(match_id=match_id, winning_team=state["winner"]))
                
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "NIGHT_ACTION" and state["phase"] == "NIGHT":
            role = state["roles"][player_id]
            target = action.get("target_id")
            if role in ["WEREWOLF", "DOCTOR", "SEER"] and target in state["alive"]:
                state["night_actions"][role] = target
                EventDispatcher.publish(NightActionEvent(match_id=match_id, actor_id=player_id, target_id=target))
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True
                
        elif action.get("type") == "SUBMIT_VOTE" and state["phase"] == "VOTING":
            target = action.get("target_id")
            if target in state["alive"]:
                state["votes"][player_id] = target
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True

        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner"]: return []
        if state["winner"] == "WEREWOLVES":
            return [p for p in state["players"] if state["roles"][p] == "WEREWOLF"]
        return [p for p in state["players"] if state["roles"][p] != "WEREWOLF"]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

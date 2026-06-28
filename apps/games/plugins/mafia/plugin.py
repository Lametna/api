import random
from typing import Dict, Any, List
from django.core.cache import cache
from apps.games.sdk.base import BaseGamePlugin
from apps.common.events import EventDispatcher
from .events import (
    RoleAssignedEvent, NightStartedEvent, NightEndedEvent,
    PlayerEliminatedEvent, VoteSubmittedEvent, GameFinishedEvent
)

class MafiaPlugin(BaseGamePlugin):
    @property
    def plugin_id(self) -> str:
        return "lametna.games.mafia"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "Mafia",
            "category": "SOCIAL_DEDUCTION",
            "min_players": 5,
            "max_players": 20,
            "has_turns": False,
            "configurable": ["mafia_count", "doctor_enabled", "detective_enabled"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    def on_match_start(self, match_id: str, players: List[str]) -> None:
        if len(players) < 5: return
        
        # Simple role distribution
        roles = ["MAFIA"] * 2 + ["DOCTOR", "DETECTIVE"] + ["CITIZEN"] * (len(players) - 4)
        random.shuffle(roles)
        
        player_roles = {p: roles[i] for i, p in enumerate(players)}
        
        state = {
            "players": players,
            "alive": players.copy(),
            "roles": player_roles,
            "phase": "NIGHT", # NIGHT, DAY, VOTING
            "round": 1,
            "night_actions": {},
            "day_votes": {},
            "winner": None
        }
        cache.set(f"match_state:{match_id}", state, timeout=3600)
        
        for p, r in player_roles.items():
            EventDispatcher.publish(RoleAssignedEvent(match_id=match_id, player_id=p, role=r))
            
        EventDispatcher.publish(NightStartedEvent(match_id=match_id, round_number=1))

    def on_round_start(self, match_id: str, round_id: str) -> None:
        pass

    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        state = cache.get(f"match_state:{match_id}")
        if not state or state["winner"] or player_id not in state["alive"]: return False
        
        phase = state["phase"]
        
        if action.get("type") == "SUBMIT_NIGHT_ACTION" and phase == "NIGHT":
            target = action.get("target_id")
            role = state["roles"][player_id]
            if target not in state["alive"] or role == "CITIZEN": return False
            
            # For Mafia, all mafias must agree, but for MVP let's assume one mafia submits kill
            state["night_actions"][role] = target
            
            # Check if all capable roles have submitted
            expected_actions = set(r for p, r in state["roles"].items() if p in state["alive"] and r != "CITIZEN")
            # For Mafia MVP, we treat 'MAFIA' as a single entity action
            
            # Just relying on host FORCE_TRANSITION to resolve night for MVP complexity
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "FORCE_TRANSITION":
            if phase == "NIGHT":
                # Resolve night
                killed = state["night_actions"].get("MAFIA")
                saved = state["night_actions"].get("DOCTOR")
                
                eliminated = killed if killed != saved else None
                if eliminated:
                    state["alive"].remove(eliminated)
                    EventDispatcher.publish(PlayerEliminatedEvent(match_id=match_id, player_id=eliminated, reason="MAFIA_KILLED"))
                    
                state["phase"] = "DAY"
                EventDispatcher.publish(NightEndedEvent(match_id=match_id, eliminated_player_id=eliminated or ""))
                
            elif phase == "DAY":
                state["phase"] = "VOTING"
                state["day_votes"] = {}
                
            elif phase == "VOTING":
                # Resolve votes
                if state["day_votes"]:
                    vote_counts = {}
                    for t in state["day_votes"].values():
                        vote_counts[t] = vote_counts.get(t, 0) + 1
                    highest_voted = max(vote_counts, key=vote_counts.get)
                    
                    state["alive"].remove(highest_voted)
                    EventDispatcher.publish(PlayerEliminatedEvent(match_id=match_id, player_id=highest_voted, reason="VOTED_OUT"))
                    
                state["phase"] = "NIGHT"
                state["round"] += 1
                state["night_actions"] = {}
                EventDispatcher.publish(NightStartedEvent(match_id=match_id, round_number=state["round"]))
                
            # Win Check
            mafias = sum(1 for p in state["alive"] if state["roles"][p] == "MAFIA")
            citizens = len(state["alive"]) - mafias
            if mafias == 0:
                state["winner"] = "CITIZENS"
            elif mafias >= citizens:
                state["winner"] = "MAFIA"
                
            if state["winner"]:
                EventDispatcher.publish(GameFinishedEvent(match_id=match_id, winning_team=state["winner"]))
                
            cache.set(f"match_state:{match_id}", state, timeout=3600)
            return True
            
        elif action.get("type") == "SUBMIT_VOTE" and phase == "VOTING":
            target = action.get("target_id")
            if target in state["alive"]:
                state["day_votes"][player_id] = target
                EventDispatcher.publish(VoteSubmittedEvent(match_id=match_id, voter_id=player_id, target_id=target))
                cache.set(f"match_state:{match_id}", state, timeout=3600)
                return True

        return False

    def evaluate_win_condition(self, match_id: str) -> List[str]:
        state = cache.get(f"match_state:{match_id}")
        if not state or not state["winner"]: return []
        if state["winner"] == "MAFIA":
            return [p for p in state["players"] if state["roles"][p] == "MAFIA"]
        return [p for p in state["players"] if state["roles"][p] != "MAFIA"]

    def on_match_finish(self, match_id: str) -> None:
        cache.delete(f"match_state:{match_id}")

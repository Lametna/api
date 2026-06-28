from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class RoleAssignedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    role: str

@dataclass
class NightActionEvent(BaseDomainEvent):
    match_id: str
    actor_id: str
    target_id: str

@dataclass
class VoteCompletedEvent(BaseDomainEvent):
    match_id: str
    eliminated_id: str

@dataclass
class PlayerEliminatedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    reason: str

@dataclass
class MatchFinishedEvent(BaseDomainEvent):
    match_id: str
    winning_team: str

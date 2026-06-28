from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class RoleAssignedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    role: str

@dataclass
class NightStartedEvent(BaseDomainEvent):
    match_id: str
    round_number: int

@dataclass
class NightEndedEvent(BaseDomainEvent):
    match_id: str
    eliminated_player_id: str # Can be None if saved

@dataclass
class PlayerEliminatedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    reason: str # E.g., 'MAFIA_KILLED', 'VOTED_OUT'

@dataclass
class VoteSubmittedEvent(BaseDomainEvent):
    match_id: str
    voter_id: str
    target_id: str

@dataclass
class GameFinishedEvent(BaseDomainEvent):
    match_id: str
    winning_team: str

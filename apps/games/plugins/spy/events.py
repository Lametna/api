from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class SpyAssignedEvent(BaseDomainEvent):
    match_id: str
    spy_ids: list # list of player_ids

@dataclass
class VoteSubmittedEvent(BaseDomainEvent):
    match_id: str
    voter_id: str
    target_id: str

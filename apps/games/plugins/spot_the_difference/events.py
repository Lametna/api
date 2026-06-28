from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class DifferenceFoundEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    difference_id: str
    score_awarded: int

@dataclass
class HintUsedEvent(BaseDomainEvent):
    match_id: str
    player_id: str

@dataclass
class RoundFinishedEvent(BaseDomainEvent):
    match_id: str
    leaderboard: dict

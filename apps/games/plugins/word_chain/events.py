from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class WordSubmittedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    word: str
    score_awarded: int

@dataclass
class TurnExpiredEvent(BaseDomainEvent):
    match_id: str
    player_id: str

@dataclass
class PlayerEliminatedEvent(BaseDomainEvent):
    match_id: str
    player_id: str

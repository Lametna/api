from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class GuessSubmittedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    guess: int

@dataclass
class NumberFoundEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    number: int
    attempts: int

from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class BingoMarkedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    number: int
    row: int
    col: int

@dataclass
class BingoCompletedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    lines_completed: int

from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class CardFlippedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    card_index: int
    card_value: str

@dataclass
class PairMatchedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    card_index_1: int
    card_index_2: int
    score_awarded: int

@dataclass
class TurnEndedEvent(BaseDomainEvent):
    match_id: str
    player_id: str

@dataclass
class GameFinishedEvent(BaseDomainEvent):
    match_id: str
    winners: list

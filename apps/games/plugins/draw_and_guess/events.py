from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class DrawingStartedEvent(BaseDomainEvent):
    match_id: str
    drawer_id: str
    round_number: int

@dataclass
class GuessSubmittedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    guess: str

@dataclass
class CorrectGuessEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    score_awarded: int

@dataclass
class RoundFinishedEvent(BaseDomainEvent):
    match_id: str
    secret_word: str

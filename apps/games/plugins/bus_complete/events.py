from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class LetterGeneratedEvent(BaseDomainEvent):
    match_id: str
    round_number: int
    letter: str

@dataclass
class AnswerSubmittedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    category: str

@dataclass
class AnswersLockedEvent(BaseDomainEvent):
    match_id: str
    round_number: int

@dataclass
class AnswerValidatedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    category: str
    is_valid: bool
    score_awarded: int

@dataclass
class RoundScoredEvent(BaseDomainEvent):
    match_id: str
    round_number: int
    leaderboard: dict

@dataclass
class BusCompletedEvent(BaseDomainEvent):
    match_id: str
    winners: list

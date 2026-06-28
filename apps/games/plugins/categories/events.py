from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class CategoryGeneratedEvent(BaseDomainEvent):
    match_id: str
    round_number: int
    category_name: str

@dataclass
class AnswerSubmittedEvent(BaseDomainEvent):
    match_id: str
    player_id: str

@dataclass
class AnswersLockedEvent(BaseDomainEvent):
    match_id: str

@dataclass
class RoundScoredEvent(BaseDomainEvent):
    match_id: str
    leaderboard: dict

from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class WordAssignedEvent(BaseDomainEvent):
    match_id: str
    actor_id: str
    word: str
    forbidden_words: list

@dataclass
class ForbiddenWordUsedEvent(BaseDomainEvent):
    match_id: str
    actor_id: str

@dataclass
class TabooWordSolvedEvent(BaseDomainEvent):
    match_id: str
    guesser_id: str
    score_awarded: int

@dataclass
class TurnEndedEvent(BaseDomainEvent):
    match_id: str
    actor_id: str
    score_delta: int

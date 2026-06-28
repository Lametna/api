from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class LetterGuessedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    letter: str
    is_correct: bool

@dataclass
class WordSolvedEvent(BaseDomainEvent):
    match_id: str
    winners: list

@dataclass
class IncorrectGuessEvent(BaseDomainEvent):
    match_id: str
    strikes: int

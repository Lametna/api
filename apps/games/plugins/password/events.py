from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class SecretWordAssignedEvent(BaseDomainEvent):
    match_id: str
    team_id: str
    clue_giver_id: str

@dataclass
class ClueSubmittedEvent(BaseDomainEvent):
    match_id: str
    clue_giver_id: str
    clue: str

@dataclass
class PasswordGuessSubmittedEvent(BaseDomainEvent):
    match_id: str
    guesser_id: str
    guess: str

@dataclass
class WordSolvedEvent(BaseDomainEvent):
    match_id: str
    team_id: str
    score_awarded: int

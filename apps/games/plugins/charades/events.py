from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class PromptAssignedEvent(BaseDomainEvent):
    match_id: str
    actor_id: str
    prompt_id: str

@dataclass
class RoundStartedEvent(BaseDomainEvent):
    match_id: str
    round_number: int

@dataclass
class PromptSolvedEvent(BaseDomainEvent):
    match_id: str
    guesser_id: str
    time_taken_secs: int

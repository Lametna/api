from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class QuestionAnsweredEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    question_id: str
    is_correct: bool
    time_taken_ms: int

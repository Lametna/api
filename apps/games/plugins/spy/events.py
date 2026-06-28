from dataclasses import dataclass
from apps.common.events import BaseDomainEvent

@dataclass
class SecretWordSelectedEvent(BaseDomainEvent):
    match_id: str
    secret_word_id: str
    category_id: str

@dataclass
class SpyAssignedEvent(BaseDomainEvent):
    match_id: str
    spy_ids: list

@dataclass
class DiscussionStartedEvent(BaseDomainEvent):
    match_id: str
    duration_secs: int

@dataclass
class VoteSubmittedEvent(BaseDomainEvent):
    match_id: str
    voter_id: str
    target_id: str

@dataclass
class VoteCompletedEvent(BaseDomainEvent):
    match_id: str
    highest_voted_id: str

@dataclass
class SpyRevealedEvent(BaseDomainEvent):
    match_id: str
    spy_ids: list

@dataclass
class RoundCompletedEvent(BaseDomainEvent):
    match_id: str
    round_number: int
    winner_team: str

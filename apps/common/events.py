import logging
import uuid
from datetime import datetime
from typing import Callable, Dict, List, Any, Type
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass(kw_only=True)
class BaseDomainEvent:
    """Base class for all domain events ensuring standardized metadata."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def event_name(self) -> str:
        return self.__class__.__name__

# --- Messaging Events ---
@dataclass
class MessageSentEvent(BaseDomainEvent):
    sender_id: str
    conversation_id: str
    content: str
    content_type: str

@dataclass
class MessageEditedEvent(BaseDomainEvent):
    message_id: str
    content: str

@dataclass
class MessageDeletedEvent(BaseDomainEvent):
    message_id: str
    conversation_id: str

@dataclass
class MessageReadEvent(BaseDomainEvent):
    message_id: str
    user_id: str

@dataclass
class TypingStartedEvent(BaseDomainEvent):
    conversation_id: str
    user_id: str

@dataclass
class TypingStoppedEvent(BaseDomainEvent):
    conversation_id: str
    user_id: str

@dataclass
class ConversationCreatedEvent(BaseDomainEvent):
    conversation_id: str
    members: List[str]

# --- Friend/Social Events ---
@dataclass
class FriendRequestSentEvent(BaseDomainEvent):
    sender_id: str
    receiver_id: str

@dataclass
class FriendAcceptedEvent(BaseDomainEvent):
    user_a_id: str
    user_b_id: str

@dataclass
class FriendRemovedEvent(BaseDomainEvent):
    user_a_id: str
    user_b_id: str

# --- Notification Events ---
@dataclass
class NotificationCreatedEvent(BaseDomainEvent):
    notification_id: str
    recipient_id: str
    type: str
    title: str

@dataclass
class NotificationReadEvent(BaseDomainEvent):
    notification_id: str
    user_id: str

# --- Presence Events ---
@dataclass
class PresenceUpdatedEvent(BaseDomainEvent):
    user_id: str
    status: str

# --- Party Events ---
@dataclass
class PartyCreatedEvent(BaseDomainEvent):
    party_id: str
    host_id: str

@dataclass
class PartyJoinedEvent(BaseDomainEvent):
    party_id: str
    user_id: str

@dataclass
class PartyLeftEvent(BaseDomainEvent):
    party_id: str
    user_id: str
    reason: str # 'left', 'kicked', 'timeout'

@dataclass
class PartyDisbandedEvent(BaseDomainEvent):
    party_id: str

@dataclass
class HostTransferredEvent(BaseDomainEvent):
    party_id: str
    old_host_id: str
    new_host_id: str

@dataclass
class PartyInviteSentEvent(BaseDomainEvent):
    party_id: str
    sender_id: str
    receiver_id: str

@dataclass
class PartyInviteAcceptedEvent(BaseDomainEvent):
    party_id: str
    user_id: str

@dataclass
class PartyReadyChangedEvent(BaseDomainEvent):
    party_id: str
    user_id: str
    is_ready: bool

@dataclass
class GameQueuedEvent(BaseDomainEvent):
    party_id: str
    game_id: str

# --- Community Events ---
@dataclass
class CommunityCreatedEvent(BaseDomainEvent):
    community_id: str
    owner_id: str

@dataclass
class CommunityJoinedEvent(BaseDomainEvent):
    community_id: str
    user_id: str

@dataclass
class CommunityLeftEvent(BaseDomainEvent):
    community_id: str
    user_id: str

@dataclass
class CommunityDeletedEvent(BaseDomainEvent):
    community_id: str

@dataclass
class CommunityMemberPromotedEvent(BaseDomainEvent):
    community_id: str
    user_id: str
    new_role: str

@dataclass
class CommunityPostCreatedEvent(BaseDomainEvent):
    community_id: str
    post_id: str
    author_id: str

@dataclass
class CommunityEventCreatedEvent(BaseDomainEvent):
    community_id: str
    event_id: str
    creator_id: str

@dataclass
class CommunityInvitationSentEvent(BaseDomainEvent):
    community_id: str
    sender_id: str
    receiver_id: str

# --- Game Platform Events ---
@dataclass
class GameRegisteredEvent(BaseDomainEvent):
    game_id: str

@dataclass
class MatchCreatedEvent(BaseDomainEvent):
    match_id: str
    game_id: str
    party_id: str

@dataclass
class MatchStartedEvent(BaseDomainEvent):
    match_id: str

@dataclass
class MatchPausedEvent(BaseDomainEvent):
    match_id: str

@dataclass
class MatchFinishedEvent(BaseDomainEvent):
    match_id: str

@dataclass
class RoundStartedEvent(BaseDomainEvent):
    match_id: str
    round_id: str

@dataclass
class RoundFinishedEvent(BaseDomainEvent):
    match_id: str
    round_id: str

@dataclass
class TurnStartedEvent(BaseDomainEvent):
    match_id: str
    turn_id: str
    player_id: str

@dataclass
class TurnFinishedEvent(BaseDomainEvent):
    match_id: str
    turn_id: str

@dataclass
class PlayerJoinedMatchEvent(BaseDomainEvent):
    match_id: str
    player_id: str

@dataclass
class PlayerLeftMatchEvent(BaseDomainEvent):
    match_id: str
    player_id: str

@dataclass
class ScoreUpdatedEvent(BaseDomainEvent):
    match_id: str
    player_id: str
    new_score: int

@dataclass
class WinConditionMetEvent(BaseDomainEvent):
    match_id: str
    winners: list # list of player_ids

# --- Progression & Reward Events ---
@dataclass
class PlayerLeveledUpEvent(BaseDomainEvent):
    player_id: str
    new_level: int
    reward_ids: list

@dataclass
class XPEarnedEvent(BaseDomainEvent):
    player_id: str
    amount: int
    reason: str

@dataclass
class AchievementUnlockedEvent(BaseDomainEvent):
    player_id: str
    achievement_id: str

@dataclass
class ChallengeCompletedEvent(BaseDomainEvent):
    player_id: str
    challenge_id: str

@dataclass
class RewardGrantedEvent(BaseDomainEvent):
    player_id: str
    reward_id: str
    reward_type: str

@dataclass
class BadgeUnlockedEvent(BaseDomainEvent):
    player_id: str
    badge_id: str

@dataclass
class TitleUnlockedEvent(BaseDomainEvent):
    player_id: str
    title_id: str

@dataclass
class StreakUpdatedEvent(BaseDomainEvent):
    player_id: str
    streak_type: str
    current_streak: int

# --- Economy Events ---
@dataclass
class CoinsGrantedEvent(BaseDomainEvent):
    player_id: str
    amount: int
    reason: str

@dataclass
class CoinsSpentEvent(BaseDomainEvent):
    player_id: str
    amount: int
    reason: str

@dataclass
class ItemPurchasedEvent(BaseDomainEvent):
    player_id: str
    item_id: str
    cost: int

@dataclass
class ItemGrantedEvent(BaseDomainEvent):
    player_id: str
    item_id: str
    source: str

@dataclass
class ItemEquippedEvent(BaseDomainEvent):
    player_id: str
    item_id: str
    slot_type: str

@dataclass
class BundlePurchasedEvent(BaseDomainEvent):
    player_id: str
    bundle_id: str
    cost: int

@dataclass
class InventoryUpdatedEvent(BaseDomainEvent):
    player_id: str
    item_id: str
    quantity: int

# --- Competitive Events ---
@dataclass
class SeasonStartedEvent(BaseDomainEvent):
    season_id: str

@dataclass
class SeasonEndedEvent(BaseDomainEvent):
    season_id: str

@dataclass
class LeaderboardUpdatedEvent(BaseDomainEvent):
    leaderboard_id: str

@dataclass
class PlayerPromotedEvent(BaseDomainEvent):
    player_id: str
    new_tier: str
    game_id: str

@dataclass
class PlayerDemotedEvent(BaseDomainEvent):
    player_id: str
    new_tier: str
    game_id: str

@dataclass
class TournamentCreatedEvent(BaseDomainEvent):
    tournament_id: str

@dataclass
class TournamentStartedEvent(BaseDomainEvent):
    tournament_id: str

@dataclass
class TournamentFinishedEvent(BaseDomainEvent):
    tournament_id: str

@dataclass
class LiveEventStartedEvent(BaseDomainEvent):
    event_id: str

@dataclass
class LiveEventEndedEvent(BaseDomainEvent):
    event_id: str

# --- Event Dispatcher ---
class EventDispatcher:
    """
    Strongly-typed Domain Event Dispatcher to decouple services.
    Services publish subclass instances of BaseDomainEvent.
    """
    _subscribers: Dict[Type[BaseDomainEvent], List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: Type[BaseDomainEvent], handler: Callable):
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        if handler not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(handler)
            
    @classmethod
    def publish(cls, event: BaseDomainEvent):
        event_type = type(event)
        logger.debug(f"Domain Event Published: {event.event_name} (ID: {event.event_id})")
        
        if event_type in cls._subscribers:
            for handler in cls._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error handling event {event.event_name} by {handler.__name__}: {str(e)}")

import logging
from typing import Tuple, List, Dict, Any
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction

from .models import FriendRequest, Friendship
from .repositories import FriendRepository, BlockRepository, PresenceRepository
from .selectors import FriendSelector, BlockSelector, PresenceSelector

logger = logging.getLogger(__name__)
User = get_user_model()

class BlockService:
    @staticmethod
    def block_user(blocker: User, blocked: User) -> Tuple[bool, str]:
        if blocker.id == blocked.id:
            return False, "You cannot block yourself."
            
        BlockRepository.block_user(blocker, blocked)
        return True, "User blocked successfully."

    @staticmethod
    def unblock_user(blocker: User, blocked: User) -> Tuple[bool, str]:
        BlockRepository.unblock_user(blocker, blocked)
        return True, "User unblocked successfully."


class FriendRequestService:
    MAX_FRIENDS = 1000

    @staticmethod
    def send_request(sender: User, receiver: User) -> Tuple[bool, str]:
        if sender.id == receiver.id:
            return False, "You cannot send a friend request to yourself."

        if BlockSelector.is_blocked(sender, receiver):
            return False, "Cannot send friend request." # Ambiguous message for privacy
            
        if FriendSelector.is_friend(sender, receiver):
            return False, "You are already friends with this user."
            
        if FriendSelector.get_friendship_count(sender) >= FriendRequestService.MAX_FRIENDS:
            return False, f"You have reached the maximum limit of {FriendRequestService.MAX_FRIENDS} friends."

        # Check existing requests
        existing_request = FriendSelector.get_request(sender, receiver)
        if existing_request and existing_request.status == FriendRequest.Status.PENDING:
            return False, "A friend request is already pending."

        reverse_request = FriendSelector.get_request(receiver, sender)
        if reverse_request and reverse_request.status == FriendRequest.Status.PENDING:
            # Auto-accept if they already sent one
            return FriendRequestService.accept_request(receiver, sender)

        FriendRepository.create_request(sender, receiver)
        from apps.common.events import EventDispatcher, FriendRequestSentEvent
        EventDispatcher.publish(FriendRequestSentEvent(sender_id=str(sender.id), receiver_id=str(receiver.id)))
        return True, "Friend request sent."

    @staticmethod
    @transaction.atomic
    def accept_request(sender: User, receiver: User) -> Tuple[bool, str]:
        req = FriendSelector.get_request(sender, receiver)
        if not req or req.status != FriendRequest.Status.PENDING:
            return False, "Friend request not found or already processed."

        if BlockSelector.is_blocked(sender, receiver):
            return False, "Cannot accept friend request."

        if FriendSelector.get_friendship_count(receiver) >= FriendRequestService.MAX_FRIENDS:
            return False, "You have reached the maximum friend limit."

        FriendRepository.update_request_status(req, FriendRequest.Status.ACCEPTED)
        FriendRepository.create_friendship(sender, receiver)
        from apps.common.events import EventDispatcher, FriendAcceptedEvent
        EventDispatcher.publish(FriendAcceptedEvent(user_a_id=str(sender.id), user_b_id=str(receiver.id)))
        return True, "Friend request accepted."

    @staticmethod
    def decline_request(sender: User, receiver: User) -> Tuple[bool, str]:
        req = FriendSelector.get_request(sender, receiver)
        if not req or req.status != FriendRequest.Status.PENDING:
            return False, "Friend request not found or already processed."

        FriendRepository.update_request_status(req, FriendRequest.Status.DECLINED)
        return True, "Friend request declined."

    @staticmethod
    def cancel_request(sender: User, receiver: User) -> Tuple[bool, str]:
        FriendRepository.cancel_request(sender, receiver)
        return True, "Friend request canceled."


class FriendService:
    @staticmethod
    def remove_friend(user1: User, user2: User) -> Tuple[bool, str]:
        if not FriendSelector.is_friend(user1, user2):
            return False, "You are not friends with this user."
            
        FriendRepository.remove_friendship(user1, user2)
        from apps.common.events import EventDispatcher, FriendRemovedEvent
        EventDispatcher.publish(FriendRemovedEvent(user_a_id=str(user1.id), user_b_id=str(user2.id)))
        return True, "Friend removed."


class SuggestionService:
    @staticmethod
    def get_suggestions(user: User, limit: int = 10) -> List[User]:
        """
        Placeholder logic for suggestions. 
        In production, this queries mutual friends, geo, and recent games.
        """
        friends = FriendSelector.get_friends(user)
        friend_ids = [f.id for f in friends] + [user.id]
        
        # Exclude blocked
        blocked = BlockSelector.get_blocked_users(user)
        friend_ids.extend([b.id for b in blocked])
        
        # Simple random users
        return list(User.objects.exclude(id__in=friend_ids)[:limit])


class PresenceService:
    HEARTBEAT_TIMEOUT = 30 # seconds

    @staticmethod
    def _get_redis_key(user_id: str) -> str:
        return f"presence:user:{user_id}"

    @classmethod
    def set_online(cls, user_id: str) -> None:
        """
        Called when a WebSocket connects or sends a heartbeat.
        """
        key = cls._get_redis_key(user_id)
        is_new = not cache.has_key(key)
        
        # Set volatile state
        cache.set(key, "ONLINE", timeout=cls.HEARTBEAT_TIMEOUT)
        
        if is_new:
            # Sync to Postgres and broadcast
            user = User.objects.filter(id=user_id).first()
            if user:
                PresenceRepository.update_presence(user, status="ONLINE")
                logger.info(f"User {user_id} is now ONLINE. Broadcasting event.")
                # TODO: Channel layer broadcast `friend.online`

    @classmethod
    def set_offline(cls, user_id: str) -> None:
        """
        Called when a WebSocket disconnects or heartbeat TTL expires.
        """
        key = cls._get_redis_key(user_id)
        cache.delete(key)
        
        user = User.objects.filter(id=user_id).first()
        if user:
            PresenceRepository.update_presence(user, status="OFFLINE")
            logger.info(f"User {user_id} is now OFFLINE. Broadcasting event.")
            # TODO: Channel layer broadcast `friend.offline`

    @classmethod
    def get_user_status(cls, user_id: str) -> str:
        """
        Fast lookup prioritizing Redis over Postgres.
        """
        status = cache.get(cls._get_redis_key(user_id))
        if status:
            return status
            
        # Fallback to DB
        user = User.objects.filter(id=user_id).first()
        if not user:
            return "OFFLINE"
            
        presence = PresenceSelector.get_presence(user)
        return presence.status

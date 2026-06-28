from django.contrib.auth import get_user_model
from django.db.models import Q
from typing import List, Optional
from .models import Friendship, FriendRequest, BlockedUser, Presence

User = get_user_model()

class FriendSelector:
    @staticmethod
    def get_friends(user: User) -> List[User]:
        # Fetch friendships where user is either user1 or user2
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        
        friends = []
        for f in friendships:
            if f.user1_id == user.id:
                friends.append(f.user2)
            else:
                friends.append(f.user1)
        return friends

    @staticmethod
    def get_pending_requests_received(user: User):
        return FriendRequest.objects.filter(receiver=user, status=FriendRequest.Status.PENDING).select_related('sender')

    @staticmethod
    def get_pending_requests_sent(user: User):
        return FriendRequest.objects.filter(sender=user, status=FriendRequest.Status.PENDING).select_related('receiver')

    @staticmethod
    def get_request(sender: User, receiver: User) -> Optional[FriendRequest]:
        return FriendRequest.objects.filter(sender=sender, receiver=receiver).order_by('-created_at').first()
        
    @staticmethod
    def is_friend(user1: User, user2: User) -> bool:
        if str(user1.id) > str(user2.id):
            user1, user2 = user2, user1
        return Friendship.objects.filter(user1=user1, user2=user2).exists()

    @staticmethod
    def get_friendship_count(user: User) -> int:
        return Friendship.objects.filter(Q(user1=user) | Q(user2=user)).count()

class BlockSelector:
    @staticmethod
    def get_blocked_users(blocker: User) -> List[User]:
        return [b.blocked for b in BlockedUser.objects.filter(blocker=blocker).select_related('blocked')]

    @staticmethod
    def is_blocked(user_a: User, user_b: User) -> bool:
        """Returns True if either user has blocked the other."""
        return BlockedUser.objects.filter(
            Q(blocker=user_a, blocked=user_b) | Q(blocker=user_b, blocked=user_a)
        ).exists()

class PresenceSelector:
    @staticmethod
    def get_presence(user: User) -> Presence:
        presence, _ = Presence.objects.get_or_create(user=user)
        return presence

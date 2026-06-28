from django.contrib.auth import get_user_model
from django.db import transaction
from typing import Optional
from .models import Friendship, FriendRequest, BlockedUser, Presence

User = get_user_model()

class FriendRepository:
    @staticmethod
    def create_request(sender: User, receiver: User) -> FriendRequest:
        return FriendRequest.objects.create(sender=sender, receiver=receiver)

    @staticmethod
    def update_request_status(request: FriendRequest, status: str) -> FriendRequest:
        request.status = status
        request.save(update_fields=['status'])
        return request

    @staticmethod
    def create_friendship(user1: User, user2: User) -> Friendship:
        # Sort to enforce lexicographical ordering constraint
        if str(user1.id) > str(user2.id):
            user1, user2 = user2, user1
            
        return Friendship.objects.get_or_create(user1=user1, user2=user2)[0]

    @staticmethod
    def remove_friendship(user1: User, user2: User) -> None:
        if str(user1.id) > str(user2.id):
            user1, user2 = user2, user1
        Friendship.objects.filter(user1=user1, user2=user2).delete()

    @staticmethod
    def cancel_request(sender: User, receiver: User) -> None:
        FriendRequest.objects.filter(sender=sender, receiver=receiver, status=FriendRequest.Status.PENDING).update(status=FriendRequest.Status.CANCELED)


class BlockRepository:
    @staticmethod
    @transaction.atomic
    def block_user(blocker: User, blocked: User) -> BlockedUser:
        # Destroy any existing friendship
        FriendRepository.remove_friendship(blocker, blocked)
        
        # Destroy any pending requests between them
        FriendRequest.objects.filter(sender=blocker, receiver=blocked).delete()
        FriendRequest.objects.filter(sender=blocked, receiver=blocker).delete()
        
        return BlockedUser.objects.get_or_create(blocker=blocker, blocked=blocked)[0]

    @staticmethod
    def unblock_user(blocker: User, blocked: User) -> None:
        BlockedUser.objects.filter(blocker=blocker, blocked=blocked).delete()


class PresenceRepository:
    @staticmethod
    def update_presence(user: User, **kwargs) -> Presence:
        presence, _ = Presence.objects.get_or_create(user=user)
        for key, value in kwargs.items():
            setattr(presence, key, value)
        presence.save()
        return presence

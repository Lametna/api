import logging
from typing import Tuple, Dict, Any, Optional
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from .models import Party, PartyMember, PartyInvitation
from .repositories import PartyRepository, MemberRepository, InvitationRepository
from .selectors import PartySelector, MemberSelector, InvitationSelector
from apps.common.events import (
    EventDispatcher, PartyCreatedEvent, PartyJoinedEvent, PartyLeftEvent,
    PartyDisbandedEvent, HostTransferredEvent, PartyInviteSentEvent,
    PartyInviteAcceptedEvent, PartyReadyChangedEvent
)
from apps.friends.selectors import BlockSelector

logger = logging.getLogger(__name__)
User = get_user_model()

class PartyService:
    @staticmethod
    def create_party(host: User, name: str, privacy: str, max_players: int = 4, password: str = None) -> Tuple[bool, Optional[Party], str]:
        # Check if user is already in an active party
        existing_party = MemberSelector.get_user_active_party(host)
        if existing_party:
            return False, None, "You are already in an active party."

        party = PartyRepository.create_party(
            host=host, name=name, privacy=privacy, max_players=max_players, password_hash=password
        )
        
        EventDispatcher.publish(PartyCreatedEvent(party_id=str(party.id), host_id=str(host.id)))
        return True, party, "Party created successfully."

    @staticmethod
    def disband_party(user: User, party_id: str) -> Tuple[bool, str]:
        party = PartySelector.get_party(party_id)
        if not party:
            return False, "Party not found."
            
        member = MemberSelector.get_member(party, user)
        if not member or member.role != PartyMember.Role.HOST:
            return False, "Only the host can disband the party."

        PartyRepository.disband_party(party)
        EventDispatcher.publish(PartyDisbandedEvent(party_id=str(party.id)))
        return True, "Party disbanded."

class HostMigrationService:
    @staticmethod
    def transfer_host(party: Party, new_host_user: User) -> bool:
        new_host_member = MemberSelector.get_member(party, new_host_user)
        if not new_host_member:
            return False
            
        current_host = MemberSelector.get_host(party)
        if current_host:
            MemberRepository.update_role(current_host, PartyMember.Role.MEMBER)
            
        MemberRepository.update_role(new_host_member, PartyMember.Role.HOST)
        
        EventDispatcher.publish(HostTransferredEvent(
            party_id=str(party.id),
            old_host_id=str(current_host.user.id) if current_host else "",
            new_host_id=str(new_host_user.id)
        ))
        return True

    @staticmethod
    def auto_migrate_host(party: Party) -> bool:
        members = MemberSelector.get_members(party)
        if not members:
            # Empty party, disband
            PartyRepository.disband_party(party)
            EventDispatcher.publish(PartyDisbandedEvent(party_id=str(party.id)))
            return False
            
        # Promote the oldest member
        oldest_member = members[0]
        return HostMigrationService.transfer_host(party, oldest_member.user)

class PartyMembershipService:
    @staticmethod
    def join_party(user: User, party_id: str, password: str = None) -> Tuple[bool, str]:
        party = PartySelector.get_party(party_id)
        if not party:
            return False, "Party not found."
            
        # Check active party
        if MemberSelector.get_user_active_party(user):
            return False, "You are already in a party."

        members = MemberSelector.get_members(party)
        if len(members) >= party.max_players:
            return False, "Party is full."

        # Block logic: cannot join if you block anyone in the party or they block you
        for member in members:
            if BlockSelector.is_blocked(user, member.user):
                return False, "You cannot join this party due to privacy settings."

        if party.privacy == Party.Privacy.PRIVATE:
            return False, "This party is private."
        elif party.privacy == Party.Privacy.PASSWORD and party.password_hash != password:
            return False, "Incorrect password."
        elif party.privacy == Party.Privacy.INVITE_ONLY:
            # Let InvitationService handle it, or check pending invites here
            if not InvitationSelector.get_pending_invite(party, user):
                return False, "You need an invitation to join this party."

        MemberRepository.add_member(party, user)
        EventDispatcher.publish(PartyJoinedEvent(party_id=str(party.id), user_id=str(user.id)))
        return True, "Joined party."

    @staticmethod
    def leave_party(user: User, party_id: str, reason: str = 'left') -> Tuple[bool, str]:
        party = PartySelector.get_party(party_id)
        if not party:
            return False, "Party not found."
            
        member = MemberSelector.get_member(party, user)
        if not member:
            return False, "You are not in this party."

        is_host = member.role == PartyMember.Role.HOST
        MemberRepository.remove_member(party, user)
        
        EventDispatcher.publish(PartyLeftEvent(party_id=str(party.id), user_id=str(user.id), reason=reason))
        
        if is_host:
            HostMigrationService.auto_migrate_host(party)
            
        return True, "Left party."

class InvitationService:
    @staticmethod
    def send_invite(sender: User, receiver: User, party_id: str) -> Tuple[bool, str]:
        party = PartySelector.get_party(party_id)
        if not party:
            return False, "Party not found."
            
        sender_member = MemberSelector.get_member(party, sender)
        if not sender_member:
            return False, "You are not in this party."
            
        if BlockSelector.is_blocked(sender, receiver):
            return False, "Cannot send invite."
            
        # Check existing invite
        if InvitationSelector.get_pending_invite(party, receiver):
            return False, "Invite already pending."
            
        expires = timezone.now() + timedelta(hours=24)
        InvitationRepository.create_invite(party, sender, receiver, expires)
        
        EventDispatcher.publish(PartyInviteSentEvent(
            party_id=str(party.id), sender_id=str(sender.id), receiver_id=str(receiver.id)
        ))
        return True, "Invite sent."

class ReadyService:
    """Pure Redis service for tracking Ready states in a party."""
    @staticmethod
    def set_ready(party_id: str, user_id: str, is_ready: bool):
        key = f"party:{party_id}:ready:{user_id}"
        if is_ready:
            cache.set(key, True, timeout=86400) # Expire in 1 day just in case
        else:
            cache.delete(key)
            
        EventDispatcher.publish(PartyReadyChangedEvent(party_id=party_id, user_id=user_id, is_ready=is_ready))
        
        # In a real scenario, we'd check if ALL members are ready here and start the 5-sec countdown

class ReconnectService:
    """Redis-backed service to handle Grace Periods for disconnected users."""
    GRACE_PERIOD_SEC = 180 # 3 minutes

    @staticmethod
    def handle_disconnect(party_id: str, user_id: str):
        # Set a grace period key in Redis
        key = f"party:{party_id}:disconnect:{user_id}"
        cache.set(key, timezone.now().timestamp(), timeout=ReconnectService.GRACE_PERIOD_SEC)
        # We don't remove them from Postgres yet. A background task or the next interaction will clear them if timeout expires.

    @staticmethod
    def handle_reconnect(party_id: str, user_id: str):
        key = f"party:{party_id}:disconnect:{user_id}"
        cache.delete(key) # Clear grace period

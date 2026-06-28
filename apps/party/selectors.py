from django.contrib.auth import get_user_model
from typing import Optional, List
from django.utils import timezone

from .models import Party, PartyMember, PartyInvitation

User = get_user_model()

class PartySelector:
    @staticmethod
    def get_party(party_id: str) -> Optional[Party]:
        return Party.objects.filter(id=party_id, is_active=True).first()

    @staticmethod
    def get_public_parties(limit: int = 20) -> List[Party]:
        return list(Party.objects.filter(privacy=Party.Privacy.PUBLIC, is_active=True).order_by('-created_at')[:limit])

class MemberSelector:
    @staticmethod
    def get_members(party: Party) -> List[PartyMember]:
        return list(PartyMember.objects.filter(party=party).select_related('user').order_by('joined_at'))

    @staticmethod
    def get_member(party: Party, user: User) -> Optional[PartyMember]:
        return PartyMember.objects.filter(party=party, user=user).first()

    @staticmethod
    def get_host(party: Party) -> Optional[PartyMember]:
        return PartyMember.objects.filter(party=party, role=PartyMember.Role.HOST).first()

    @staticmethod
    def get_user_active_party(user: User) -> Optional[Party]:
        member = PartyMember.objects.filter(user=user, party__is_active=True).select_related('party').first()
        return member.party if member else None

class InvitationSelector:
    @staticmethod
    def get_pending_invite(party: Party, receiver: User) -> Optional[PartyInvitation]:
        return PartyInvitation.objects.filter(
            party=party, receiver=receiver, status=PartyInvitation.Status.PENDING
        ).first()

    @staticmethod
    def get_user_invites(user: User) -> List[PartyInvitation]:
        return list(PartyInvitation.objects.filter(
            receiver=user, 
            status=PartyInvitation.Status.PENDING,
            expires_at__gt=timezone.now()
        ).select_related('party', 'sender').order_by('-created_at'))

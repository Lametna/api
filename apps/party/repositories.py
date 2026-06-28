from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from typing import Optional, List, Dict, Any

from .models import Party, PartyMember, PartyInvitation, PartySession

User = get_user_model()

class PartyRepository:
    @staticmethod
    @transaction.atomic
    def create_party(host: User, name: str, privacy: str, max_players: int = 4, **kwargs) -> Party:
        party = Party.objects.create(
            name=name,
            privacy=privacy,
            max_players=max_players,
            **kwargs
        )
        PartyMember.objects.create(
            party=party,
            user=host,
            role=PartyMember.Role.HOST
        )
        PartySession.objects.create(party=party)
        return party

    @staticmethod
    def update_party(party: Party, **kwargs) -> Party:
        for key, value in kwargs.items():
            setattr(party, key, value)
        party.save()
        return party

    @staticmethod
    @transaction.atomic
    def disband_party(party: Party) -> None:
        party.is_active = False
        party.save(update_fields=['is_active'])
        session = party.sessions.filter(ended_at__isnull=True).first()
        if session:
            session.ended_at = timezone.now()
            session.save(update_fields=['ended_at'])


class MemberRepository:
    @staticmethod
    def add_member(party: Party, user: User, role: str = PartyMember.Role.MEMBER) -> PartyMember:
        return PartyMember.objects.create(party=party, user=user, role=role)

    @staticmethod
    def remove_member(party: Party, user: User) -> None:
        PartyMember.objects.filter(party=party, user=user).delete()

    @staticmethod
    def update_role(member: PartyMember, role: str) -> PartyMember:
        member.role = role
        member.save(update_fields=['role'])
        return member


class InvitationRepository:
    @staticmethod
    def create_invite(party: Party, sender: User, receiver: User, expires_at: timezone.datetime) -> PartyInvitation:
        return PartyInvitation.objects.create(
            party=party, sender=sender, receiver=receiver, expires_at=expires_at
        )

    @staticmethod
    def update_status(invite: PartyInvitation, status: str) -> PartyInvitation:
        invite.status = status
        invite.save(update_fields=['status'])
        return invite

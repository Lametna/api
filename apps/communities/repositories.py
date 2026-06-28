from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from typing import Optional

from .models import Community, CommunityMember, CommunityPost, CommunityComment, CommunityEvent, CommunityBan, CommunityInvitation

User = get_user_model()

class CommunityRepository:
    @staticmethod
    @transaction.atomic
    def create_community(owner: User, name: str, privacy: str, **kwargs) -> Community:
        community = Community.objects.create(name=name, privacy=privacy, **kwargs)
        CommunityMember.objects.create(
            community=community,
            user=owner,
            role=CommunityMember.Role.OWNER
        )
        return community

    @staticmethod
    def update_community(community: Community, **kwargs) -> Community:
        for k, v in kwargs.items():
            setattr(community, k, v)
        community.save()
        return community

    @staticmethod
    def delete_community(community: Community) -> None:
        # Soft delete or hard delete based on requirements. Let's do hard delete for MVP.
        community.delete()

class MembershipRepository:
    @staticmethod
    def add_member(community: Community, user: User, role: str = CommunityMember.Role.MEMBER) -> CommunityMember:
        return CommunityMember.objects.create(community=community, user=user, role=role)

    @staticmethod
    def remove_member(community: Community, user: User) -> None:
        CommunityMember.objects.filter(community=community, user=user).delete()

    @staticmethod
    def update_role(member: CommunityMember, role: str) -> CommunityMember:
        member.role = role
        member.save(update_fields=['role'])
        return member

    @staticmethod
    def ban_member(community: Community, user: User, banned_by: User, reason: str = "") -> CommunityBan:
        # Remove them from community first
        MembershipRepository.remove_member(community, user)
        return CommunityBan.objects.create(
            community=community, user=user, banned_by=banned_by, reason=reason
        )

    @staticmethod
    def unban_member(community: Community, user: User) -> None:
        CommunityBan.objects.filter(community=community, user=user).delete()

class PostRepository:
    @staticmethod
    def create_post(community: Community, author: User, content: str, post_type: str = CommunityPost.Type.TEXT) -> CommunityPost:
        return CommunityPost.objects.create(
            community=community, author=author, content=content, type=post_type
        )

    @staticmethod
    def soft_delete_post(post: CommunityPost) -> None:
        post.is_deleted = True
        post.save(update_fields=['is_deleted'])

class CommentRepository:
    @staticmethod
    def create_comment(post: CommunityPost, author: User, content: str, parent: Optional[CommunityComment] = None) -> CommunityComment:
        return CommunityComment.objects.create(
            post=post, author=author, content=content, parent_comment=parent
        )

class EventRepository:
    @staticmethod
    def create_event(community: Community, creator: User, title: str, description: str, start_time: timezone.datetime, end_time: Optional[timezone.datetime] = None) -> CommunityEvent:
        return CommunityEvent.objects.create(
            community=community, creator=creator, title=title,
            description=description, start_time=start_time, end_time=end_time
        )

import logging
from typing import Tuple, Optional
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Community, CommunityMember, CommunityPost, CommunityEvent
from .repositories import CommunityRepository, MembershipRepository, PostRepository, EventRepository
from .selectors import CommunitySelector, MembershipSelector, PostSelector
from apps.common.events import (
    EventDispatcher, CommunityCreatedEvent, CommunityJoinedEvent, CommunityLeftEvent,
    CommunityMemberPromotedEvent, CommunityPostCreatedEvent, CommunityEventCreatedEvent
)

logger = logging.getLogger(__name__)
User = get_user_model()

class CommunityService:
    @staticmethod
    def create_community(owner: User, name: str, privacy: str, **kwargs) -> Tuple[bool, Optional[Community], str]:
        # Check if name is taken
        if Community.objects.filter(name__iexact=name).exists():
            return False, None, "A community with this name already exists."

        community = CommunityRepository.create_community(owner, name, privacy, **kwargs)
        
        # Prepare the Community Chat Channel
        from apps.messaging.models import Conversation
        Conversation.objects.create(is_group=True, name=f"{name} General", community=community)
        
        EventDispatcher.publish(CommunityCreatedEvent(community_id=str(community.id), owner_id=str(owner.id)))
        return True, community, "Community created."

class MembershipService:
    @staticmethod
    def join_community(user: User, community_id: str, password: str = None) -> Tuple[bool, str]:
        community = CommunitySelector.get_community(community_id)
        if not community:
            return False, "Community not found."

        if MembershipSelector.get_member(community, user):
            return False, "You are already a member."

        if MembershipSelector.is_banned(community, user):
            return False, "You are banned from this community."

        if community.privacy == Community.Privacy.PRIVATE:
            return False, "This community is private."
        elif community.privacy == Community.Privacy.PASSWORD and community.password_hash != password:
            return False, "Incorrect password."
        elif community.privacy == Community.Privacy.INVITE_ONLY:
            return False, "You need an invitation to join this community."

        MembershipRepository.add_member(community, user)
        EventDispatcher.publish(CommunityJoinedEvent(community_id=str(community.id), user_id=str(user.id)))
        return True, "Joined community."

    @staticmethod
    def leave_community(user: User, community_id: str) -> Tuple[bool, str]:
        community = CommunitySelector.get_community(community_id)
        if not community:
            return False, "Community not found."

        member = MembershipSelector.get_member(community, user)
        if not member:
            return False, "You are not a member."

        if member.role == CommunityMember.Role.OWNER:
            return False, "The owner cannot leave. Transfer ownership first or delete the community."

        MembershipRepository.remove_member(community, user)
        EventDispatcher.publish(CommunityLeftEvent(community_id=str(community.id), user_id=str(user.id)))
        return True, "Left community."

class ModerationService:
    @staticmethod
    def _has_permission(actor_role: str, target_role: str) -> bool:
        hierarchy = {
            CommunityMember.Role.OWNER: 4,
            CommunityMember.Role.ADMIN: 3,
            CommunityMember.Role.MODERATOR: 2,
            CommunityMember.Role.MEMBER: 1
        }
        return hierarchy.get(actor_role, 0) > hierarchy.get(target_role, 0)

    @staticmethod
    def ban_member(actor: User, target_user: User, community_id: str, reason: str = "") -> Tuple[bool, str]:
        community = CommunitySelector.get_community(community_id)
        if not community:
            return False, "Community not found."

        actor_member = MembershipSelector.get_member(community, actor)
        target_member = MembershipSelector.get_member(community, target_user)

        if not actor_member or actor_member.role not in [CommunityMember.Role.OWNER, CommunityMember.Role.ADMIN, CommunityMember.Role.MODERATOR]:
            return False, "You do not have permission to ban."

        if target_member and not ModerationService._has_permission(actor_member.role, target_member.role):
            return False, "You cannot ban a member with equal or higher rank."

        MembershipRepository.ban_member(community, target_user, actor, reason)
        EventDispatcher.publish(CommunityLeftEvent(community_id=str(community.id), user_id=str(target_user.id)))
        return True, "Member banned."

class PostService:
    @staticmethod
    def create_post(author: User, community_id: str, content: str, post_type: str = CommunityPost.Type.TEXT) -> Tuple[bool, Optional[CommunityPost], str]:
        community = CommunitySelector.get_community(community_id)
        if not community:
            return False, None, "Community not found."

        member = MembershipSelector.get_member(community, author)
        if not member:
            return False, None, "You must be a member to post."

        # RBAC Check for Announcements
        if post_type == CommunityPost.Type.ANNOUNCEMENT and member.role not in [CommunityMember.Role.OWNER, CommunityMember.Role.ADMIN]:
            return False, None, "Only Admins can post Announcements."

        post = PostRepository.create_post(community, author, content, post_type)
        EventDispatcher.publish(CommunityPostCreatedEvent(community_id=str(community.id), post_id=str(post.id), author_id=str(author.id)))
        return True, post, "Post created."

class EventService:
    @staticmethod
    def create_event(creator: User, community_id: str, title: str, description: str, start_time) -> Tuple[bool, Optional[CommunityEvent], str]:
        community = CommunitySelector.get_community(community_id)
        if not community:
            return False, None, "Community not found."

        member = MembershipSelector.get_member(community, creator)
        if not member or member.role not in [CommunityMember.Role.OWNER, CommunityMember.Role.ADMIN, CommunityMember.Role.MODERATOR]:
            return False, None, "You do not have permission to create events."

        event = EventRepository.create_event(community, creator, title, description, start_time)
        EventDispatcher.publish(CommunityEventCreatedEvent(community_id=str(community.id), event_id=str(event.id), creator_id=str(creator.id)))
        return True, event, "Event created."

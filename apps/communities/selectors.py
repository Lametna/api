from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from typing import Optional, List

from .models import Community, CommunityMember, CommunityPost, CommunityComment, CommunityEvent, CommunityBan, CommunityInvitation

User = get_user_model()

class CommunitySelector:
    @staticmethod
    def get_community(community_id: str) -> Optional[Community]:
        return Community.objects.filter(id=community_id, is_active=True).first()

    @staticmethod
    def search_communities(query: str, limit: int = 20) -> List[Community]:
        # Basic DB search. Designed to be swapped with OpenSearch later.
        return list(Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            privacy=Community.Privacy.PUBLIC,
            is_active=True
        ).order_by('-created_at')[:limit])

    @staticmethod
    def get_trending_communities(limit: int = 10) -> List[Community]:
        # Mock trending algorithm: most members
        return list(Community.objects.filter(privacy=Community.Privacy.PUBLIC, is_active=True)
                    .annotate(member_count=Count('members'))
                    .order_by('-member_count')[:limit])

class MembershipSelector:
    @staticmethod
    def get_member(community: Community, user: User) -> Optional[CommunityMember]:
        return CommunityMember.objects.filter(community=community, user=user).first()

    @staticmethod
    def get_members(community: Community, limit: int = 50) -> List[CommunityMember]:
        return list(CommunityMember.objects.filter(community=community).select_related('user')[:limit])

    @staticmethod
    def is_banned(community: Community, user: User) -> bool:
        return CommunityBan.objects.filter(community=community, user=user).exists()

class PostSelector:
    @staticmethod
    def get_posts(community: Community, limit: int = 50) -> List[CommunityPost]:
        return list(CommunityPost.objects.filter(community=community, is_deleted=False)
                    .select_related('author')
                    .order_by('-is_pinned', '-created_at')[:limit])

    @staticmethod
    def get_post(post_id: str) -> Optional[CommunityPost]:
        return CommunityPost.objects.filter(id=post_id, is_deleted=False).first()

class EventSelector:
    @staticmethod
    def get_upcoming_events(community: Community, limit: int = 10) -> List[CommunityEvent]:
        return list(CommunityEvent.objects.filter(
            community=community, 
            start_time__gt=timezone.now()
        ).order_by('start_time')[:limit])

class FeedSelector:
    @staticmethod
    def get_unified_feed(community: Community, limit: int = 50) -> List[dict]:
        # Fetch posts and events
        posts = PostSelector.get_posts(community, limit=limit)
        events = list(CommunityEvent.objects.filter(community=community).order_by('-created_at')[:limit])
        
        # Merge and sort in memory by created_at descending
        feed = []
        for p in posts:
            feed.append({'item_type': 'POST', 'item': p, 'sort_date': p.created_at})
        for e in events:
            feed.append({'item_type': 'EVENT', 'item': e, 'sort_date': e.created_at})
            
        feed.sort(key=lambda x: x['sort_date'], reverse=True)
        return feed[:limit]

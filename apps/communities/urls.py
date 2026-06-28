from django.urls import path
from .views import (
    CommunityListView, CommunityDetailView, CommunityJoinView, CommunityPostListView, CommunityFeedView
)

app_name = 'communities'

urlpatterns = [
    path('', CommunityListView.as_view(), name='community_list'),
    path('<uuid:pk>/', CommunityDetailView.as_view(), name='community_detail'),
    path('<uuid:pk>/join/', CommunityJoinView.as_view(), name='community_join'),
    path('<uuid:pk>/posts/', CommunityPostListView.as_view(), name='community_posts'),
    path('<uuid:pk>/feed/', CommunityFeedView.as_view(), name='community_feed'),
]

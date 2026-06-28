from django.urls import path
from .views import (
    FriendsListView, FriendRemoveView, FriendRequestView, 
    FriendRequestActionView, PendingRequestsView, BlockedUsersView,
    UnblockUserView, SearchFriendsView, SuggestionsView, PresenceMeView
)

app_name = 'friends'

urlpatterns = [
    path('', FriendsListView.as_view(), name='friends_list'),
    path('<uuid:user_id>/', FriendRemoveView.as_view(), name='friend_remove'),
    
    path('request/', FriendRequestView.as_view(), name='friend_request'),
    path('<str:action>/', FriendRequestActionView.as_view(), name='friend_action'), # accept/decline/cancel
    
    path('requests/pending/', PendingRequestsView.as_view(), name='pending_requests'),
    
    path('block/list/', BlockedUsersView.as_view(), name='blocked_list'),
    path('block/', BlockedUsersView.as_view(), name='block_user'),
    path('block/<uuid:user_id>/', UnblockUserView.as_view(), name='unblock_user'),
    
    path('search/users/', SearchFriendsView.as_view(), name='search_users'),
    path('suggestions/', SuggestionsView.as_view(), name='friend_suggestions'),
    
    path('presence/me/', PresenceMeView.as_view(), name='presence_me'),
]

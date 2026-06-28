from django.urls import path
from .views import (
    PartyListView, PartyDetailView, PartyJoinView, PartyLeaveView, PartyInviteView, PartyReadyView
)

app_name = 'party'

urlpatterns = [
    path('', PartyListView.as_view(), name='party_list'),
    path('<uuid:party_id>/', PartyDetailView.as_view(), name='party_detail'),
    path('<uuid:party_id>/join/', PartyJoinView.as_view(), name='party_join'),
    path('<uuid:party_id>/leave/', PartyLeaveView.as_view(), name='party_leave'),
    path('<uuid:party_id>/invite/', PartyInviteView.as_view(), name='party_invite'),
    path('<uuid:party_id>/ready/', PartyReadyView.as_view(), name='party_ready'),
]

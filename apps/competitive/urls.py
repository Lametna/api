from django.urls import path
from .views import (
    LeaderboardListView, LeaderboardDetailView, LeaderboardEntriesView,
    RankingView, SeasonListView, SeasonCurrentView, EventListView,
    TournamentListView, TournamentDetailView, TournamentRegisterView, TournamentBracketView,
    CompetitiveStatisticsView
)

app_name = 'competitive'

urlpatterns = [
    # Leaderboards
    path('leaderboards/', LeaderboardListView.as_view(), name='leaderboards'),
    path('leaderboards/<uuid:pk>/', LeaderboardDetailView.as_view(), name='leaderboard_detail'),
    path('leaderboards/<uuid:pk>/entries/', LeaderboardEntriesView.as_view(), name='leaderboard_entries'),
    
    # Ranking
    path('ranking/', RankingView.as_view(), name='ranking'),
    
    # Seasons
    path('seasons/', SeasonListView.as_view(), name='seasons'),
    path('seasons/current/', SeasonCurrentView.as_view(), name='season_current'),
    
    # Events
    path('events/', EventListView.as_view(), name='events'),
    
    # Tournaments
    path('tournaments/', TournamentListView.as_view(), name='tournaments'),
    path('tournaments/<uuid:pk>/', TournamentDetailView.as_view(), name='tournament_detail'),
    path('tournaments/<uuid:pk>/register/', TournamentRegisterView.as_view(), name='tournament_register'),
    path('tournaments/<uuid:pk>/bracket/', TournamentBracketView.as_view(), name='tournament_bracket'),
    
    # Stats
    path('competitive/statistics/', CompetitiveStatisticsView.as_view(), name='statistics'),
]

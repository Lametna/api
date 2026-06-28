from django.urls import path
from .views import (
    GameListView, MatchListView, MatchDetailView, MatchActionView, MatchScoresView
)

app_name = 'games'

urlpatterns = [
    path('games/', GameListView.as_view(), name='game_list'),
    path('matches/', MatchListView.as_view(), name='match_list'),
    path('matches/<uuid:pk>/', MatchDetailView.as_view(), name='match_detail'),
    path('matches/<uuid:pk>/<str:action>/', MatchActionView.as_view(), name='match_action'), # handles join, start, pause, finish
    path('matches/<uuid:pk>/scores/', MatchScoresView.as_view(), name='match_scores'),
]

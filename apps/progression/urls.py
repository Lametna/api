from django.urls import path
from .views import (
    ProgressionView, StatisticsView, AchievementsView, ChallengesView, BadgesView, TitlesView
)

app_name = 'progression'

urlpatterns = [
    path('progression/', ProgressionView.as_view(), name='progress_summary'),
    path('progression/statistics/', StatisticsView.as_view(), name='statistics'),
    path('achievements/', AchievementsView.as_view(), name='achievements'),
    path('challenges/', ChallengesView.as_view(), name='challenges'),
    path('badges/', BadgesView.as_view(), name='badges'),
    path('titles/', TitlesView.as_view(), name='titles'),
]

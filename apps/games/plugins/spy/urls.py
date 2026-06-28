from django.urls import path
from .views import SpyPacksView, SpyCategoriesView, SpyConfigSchemaView

app_name = 'spy_plugin'

urlpatterns = [
    path('packs/', SpyPacksView.as_view(), name='spy_packs'),
    path('categories/', SpyCategoriesView.as_view(), name='spy_categories'),
    path('config/', SpyConfigSchemaView.as_view(), name='spy_config_schema'),
]

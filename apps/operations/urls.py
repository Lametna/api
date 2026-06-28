from django.urls import path
from .views import FeatureFlagsView

app_name = 'operations'

urlpatterns = [
    path('operations/flags/', FeatureFlagsView.as_view(), name='feature_flags'),
]

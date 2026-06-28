from django.urls import path
from .views import (
    NotificationListView, NotificationReadView, NotificationReadAllView,
    NotificationPreferenceView
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<uuid:notification_id>/', NotificationReadView.as_view(), name='notification_detail'),
    path('read-all/', NotificationReadAllView.as_view(), name='notification_read_all'),
    
    path('preferences/', NotificationPreferenceView.as_view(), name='notification_preferences'),
]

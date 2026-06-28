from django.urls import path
from .views import (
    ConversationListView, MessageListView, MessageDetailView,
    MessageReadView, TypingIndicatorView
)

app_name = 'messaging'

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversations'),
    path('conversations/<uuid:conversation_id>/messages/', MessageListView.as_view(), name='messages_list'),
    path('conversations/<uuid:conversation_id>/typing/', TypingIndicatorView.as_view(), name='typing'),
    
    path('messages/<uuid:message_id>/', MessageDetailView.as_view(), name='message_detail'),
    path('messages/<uuid:message_id>/read/', MessageReadView.as_view(), name='message_read'),
]

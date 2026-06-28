from rest_framework import serializers
from .models import Notification, NotificationPreference
from apps.users.serializers import PublicProfileSerializer

class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'type', 'priority', 'title', 'body', 'action_url', 'is_read', 'created_at', 'sender']

    def get_sender(self, obj):
        if not obj.sender:
            return None
        return {"id": obj.sender.id, "display_name": obj.sender.display_name, "avatar": obj.sender.avatar}

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        exclude = ['user']

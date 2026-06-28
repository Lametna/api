from rest_framework import serializers
from apps.games.models import SecretWordPack, SecretCategory

class SecretCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecretCategory
        fields = ['id', 'name', 'icon']

class SecretWordPackSerializer(serializers.ModelSerializer):
    categories = SecretCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = SecretWordPack
        fields = ['id', 'name', 'description', 'is_premium', 'categories']

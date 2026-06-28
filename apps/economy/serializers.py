from rest_framework import serializers
from .models import (
    Wallet, WalletTransaction, CatalogCategory, CatalogItem, CatalogBundle,
    ShopRotation, InventoryItem, EquippedItem
)

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['amount', 'transaction_type', 'reason', 'reference_id', 'created_at']

class CatalogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogCategory
        fields = ['id', 'name', 'description']

class CatalogItemSerializer(serializers.ModelSerializer):
    category = CatalogCategorySerializer(read_only=True)
    
    class Meta:
        model = CatalogItem
        fields = ['id', 'sku', 'name', 'description', 'category', 'item_type', 'price', 'is_purchasable', 'metadata']

class CatalogBundleSerializer(serializers.ModelSerializer):
    item = CatalogItemSerializer(read_only=True)
    contents = CatalogItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = CatalogBundle
        fields = ['id', 'item', 'contents', 'discount_percentage']

class InventoryItemSerializer(serializers.ModelSerializer):
    item = CatalogItemSerializer(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = ['id', 'item', 'quantity', 'acquired_at', 'is_favorite']

class EquippedItemSerializer(serializers.ModelSerializer):
    item = CatalogItemSerializer(read_only=True)
    
    class Meta:
        model = EquippedItem
        fields = ['id', 'item', 'slot_type', 'equipped_at']

class PurchaseRequestSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()

class EquipRequestSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()

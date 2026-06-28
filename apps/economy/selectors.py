from typing import List, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Wallet, WalletTransaction, CatalogCategory, CatalogItem, CatalogBundle,
    ShopRotation, InventoryItem, EquippedItem, Purchase
)

User = get_user_model()

class WalletSelector:
    @staticmethod
    def get_wallet(user: User) -> Optional[Wallet]:
        return Wallet.objects.filter(user=user).first()
        
    @staticmethod
    def get_transactions(user: User) -> List[WalletTransaction]:
        return list(WalletTransaction.objects.filter(wallet__user=user).order_by('-created_at')[:50])

class CatalogSelector:
    @staticmethod
    def get_categories() -> List[CatalogCategory]:
        return list(CatalogCategory.objects.all())

    @staticmethod
    def get_items() -> List[CatalogItem]:
        return list(CatalogItem.objects.all())
        
    @staticmethod
    def get_item(item_id: str) -> Optional[CatalogItem]:
        return CatalogItem.objects.filter(id=item_id).first()
        
    @staticmethod
    def get_bundles() -> List[CatalogBundle]:
        return list(CatalogBundle.objects.select_related('item').prefetch_related('contents'))

class ShopSelector:
    @staticmethod
    def get_active_shop() -> Optional[ShopRotation]:
        now = timezone.now()
        return ShopRotation.objects.filter(start_time__lte=now, end_time__gte=now, is_active=True).first()
        
    @staticmethod
    def get_featured_items() -> List[CatalogItem]:
        shop = ShopSelector.get_active_shop()
        if shop:
            return list(shop.items.all())
        return []

class InventorySelector:
    @staticmethod
    def get_inventory(user: User) -> List[InventoryItem]:
        return list(InventoryItem.objects.filter(user=user).select_related('item'))
        
    @staticmethod
    def has_item(user: User, item: CatalogItem) -> bool:
        return InventoryItem.objects.filter(user=user, item=item).exists()

class EquipmentSelector:
    @staticmethod
    def get_equipped_items(user: User) -> List[EquippedItem]:
        return list(EquippedItem.objects.filter(user=user).select_related('item'))

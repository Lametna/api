from typing import Tuple, Dict, Any
from django.contrib.auth import get_user_model

from .models import CatalogItem
from .repositories import WalletRepository, InventoryRepository, EquipmentRepository, PurchaseRepository
from .selectors import InventorySelector, WalletSelector, CatalogSelector
from apps.common.events import (
    EventDispatcher, CoinsGrantedEvent, CoinsSpentEvent, ItemGrantedEvent,
    ItemEquippedEvent, ItemPurchasedEvent, BundlePurchasedEvent
)

User = get_user_model()

class WalletService:
    @staticmethod
    def credit(user: User, amount: int, reason: str, ref_id: str = "") -> None:
        if amount > 0:
            WalletRepository.credit(user, amount, reason, ref_id)
            EventDispatcher.publish(CoinsGrantedEvent(player_id=str(user.id), amount=amount, reason=reason))

    @staticmethod
    def debit(user: User, amount: int, reason: str, ref_id: str = "") -> bool:
        if amount <= 0: return False
        success, _ = WalletRepository.debit(user, amount, reason, ref_id)
        if success:
            EventDispatcher.publish(CoinsSpentEvent(player_id=str(user.id), amount=amount, reason=reason))
        return success

class InventoryService:
    @staticmethod
    def grant_item(user: User, item: CatalogItem, quantity: int = 1, source: str = "") -> None:
        if item.is_unique and InventorySelector.has_item(user, item):
            # Duplicate item logic: fallback to coins grant
            fallback_coins = int(item.price * 0.2) if item.price > 0 else 50
            WalletService.credit(user, fallback_coins, f"DUPLICATE_ITEM_CONVERSION_{item.sku}")
            return
            
        InventoryRepository.grant_item(user, item, quantity)
        EventDispatcher.publish(ItemGrantedEvent(player_id=str(user.id), item_id=str(item.id), source=source))

class EquipmentService:
    @staticmethod
    def equip(user: User, item_id: str) -> Tuple[bool, str]:
        item = CatalogSelector.get_item(item_id)
        if not item: return False, "Item not found."
        
        if not InventorySelector.has_item(user, item):
            return False, "You do not own this item."
            
        EquipmentRepository.equip_item(user, item)
        EventDispatcher.publish(ItemEquippedEvent(player_id=str(user.id), item_id=str(item.id), slot_type=item.item_type))
        return True, "Item equipped."

class PurchaseService:
    @staticmethod
    def purchase_item(user: User, item_id: str) -> Tuple[bool, str]:
        item = CatalogSelector.get_item(item_id)
        if not item or not item.is_purchasable:
            return False, "Item not available for purchase."
            
        if item.is_unique and InventorySelector.has_item(user, item):
            return False, "You already own this item."
            
        # Wallet debit locks the row
        if not WalletService.debit(user, item.price, f"PURCHASE_{item.sku}", str(item.id)):
            return False, "Insufficient balance."
            
        # Log purchase
        PurchaseRepository.log_purchase(user, item, item.price)
        
        # Grant item
        InventoryService.grant_item(user, item, 1, "SHOP_PURCHASE")
        
        EventDispatcher.publish(ItemPurchasedEvent(player_id=str(user.id), item_id=str(item.id), cost=item.price))
        return True, "Purchase successful."

from typing import Dict, Any, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import (
    Wallet, WalletTransaction, CatalogItem, InventoryItem, EquippedItem, Purchase
)

User = get_user_model()

class WalletRepository:
    @staticmethod
    def get_or_create_wallet(user: User) -> Wallet:
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    @staticmethod
    def credit(user: User, amount: int, reason: str, ref_id: str = "") -> Wallet:
        with transaction.atomic():
            # Use select_for_update to prevent race conditions on balance
            wallet = Wallet.objects.select_for_update().get(user=user)
            wallet.balance += amount
            wallet.save(update_fields=['balance'])
            
            WalletTransaction.objects.create(
                wallet=wallet, amount=amount, transaction_type=WalletTransaction.Type.CREDIT,
                reason=reason, reference_id=ref_id
            )
            return wallet

    @staticmethod
    def debit(user: User, amount: int, reason: str, ref_id: str = "") -> Tuple[bool, Wallet]:
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=user)
            if wallet.balance < amount:
                return False, wallet
                
            wallet.balance -= amount
            wallet.save(update_fields=['balance'])
            
            WalletTransaction.objects.create(
                wallet=wallet, amount=amount, transaction_type=WalletTransaction.Type.DEBIT,
                reason=reason, reference_id=ref_id
            )
            return True, wallet

class InventoryRepository:
    @staticmethod
    def grant_item(user: User, item: CatalogItem, quantity: int = 1) -> InventoryItem:
        inv_item, created = InventoryItem.objects.get_or_create(user=user, item=item)
        if not created:
            inv_item.quantity += quantity
            inv_item.save(update_fields=['quantity'])
        return inv_item

class EquipmentRepository:
    @staticmethod
    def equip_item(user: User, item: CatalogItem) -> EquippedItem:
        equipped, _ = EquippedItem.objects.update_or_create(
            user=user, slot_type=item.item_type,
            defaults={'item': item}
        )
        return equipped

class PurchaseRepository:
    @staticmethod
    def log_purchase(user: User, item: CatalogItem, cost: int) -> Purchase:
        return Purchase.objects.create(user=user, item=item, cost=cost)

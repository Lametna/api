from django.db import models
from django.conf import settings
from core.models import BaseModel

User = settings.AUTH_USER_MODEL

class Wallet(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user} - {self.balance} Coins"

class WalletTransaction(BaseModel):
    class Type(models.TextChoices):
        CREDIT = 'CREDIT', 'Credit'
        DEBIT = 'DEBIT', 'Debit'
        
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=Type.choices)
    reason = models.CharField(max_length=100) # e.g., PURCHASE, REWARD, COMP
    reference_id = models.CharField(max_length=100, blank=True) # e.g., Purchase ID or Match ID
    created_at = models.DateTimeField(auto_now_add=True)

class CatalogCategory(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

class CatalogItem(BaseModel):
    class Type(models.TextChoices):
        AVATAR = 'AVATAR', 'Avatar'
        BANNER = 'BANNER', 'Banner'
        BADGE = 'BADGE', 'Badge'
        TITLE = 'TITLE', 'Title'
        FRAME = 'FRAME', 'Avatar Frame'
        THEME = 'THEME', 'Theme'
        DECORATION = 'DECORATION', 'Profile Decoration'
        EMOTE = 'EMOTE', 'Emote'
        BUNDLE = 'BUNDLE', 'Bundle'
        
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(CatalogCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    item_type = models.CharField(max_length=20, choices=Type.choices)
    price = models.IntegerField(default=0)
    is_purchasable = models.BooleanField(default=True)
    is_unique = models.BooleanField(default=True) # True for cosmetics, False for consumables
    metadata = models.JSONField(default=dict, blank=True) # visual assets, color codes, etc.

class CatalogBundle(BaseModel):
    item = models.OneToOneField(CatalogItem, on_delete=models.CASCADE, related_name='bundle_info')
    contents = models.ManyToManyField(CatalogItem, related_name='part_of_bundles')
    discount_percentage = models.IntegerField(default=0)

class ShopRotation(BaseModel):
    name = models.CharField(max_length=100)
    items = models.ManyToManyField(CatalogItem, related_name='rotations')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

class InventoryItem(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(CatalogItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    acquired_at = models.DateTimeField(auto_now_add=True)
    is_favorite = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'item')

class EquippedItem(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment')
    item = models.ForeignKey(CatalogItem, on_delete=models.CASCADE)
    slot_type = models.CharField(max_length=20) # matches CatalogItem.Type usually
    equipped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'slot_type')

class Purchase(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    item = models.ForeignKey(CatalogItem, on_delete=models.SET_NULL, null=True)
    cost = models.IntegerField()
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_refunded = models.BooleanField(default=False)

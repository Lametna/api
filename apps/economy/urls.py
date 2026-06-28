from django.urls import path
from .views import (
    WalletView, WalletTransactionsView, CatalogListView, CatalogDetailView,
    BundleListView, ShopFeaturedView, ShopPurchaseView, InventoryListView,
    EquipmentEquipView
)

app_name = 'economy'

urlpatterns = [
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('wallet/transactions/', WalletTransactionsView.as_view(), name='wallet_transactions'),
    
    path('catalog/', CatalogListView.as_view(), name='catalog_list'),
    path('catalog/<uuid:pk>/', CatalogDetailView.as_view(), name='catalog_detail'),
    path('bundles/', BundleListView.as_view(), name='bundle_list'),
    
    path('shop/', ShopFeaturedView.as_view(), name='shop_featured'),
    path('shop/purchase/', ShopPurchaseView.as_view(), name='shop_purchase'),
    
    path('inventory/', InventoryListView.as_view(), name='inventory_list'),
    path('inventory/equip/', EquipmentEquipView.as_view(), name='equipment_equip'),
]

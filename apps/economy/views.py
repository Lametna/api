from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .serializers import (
    WalletSerializer, WalletTransactionSerializer, CatalogItemSerializer,
    CatalogBundleSerializer, InventoryItemSerializer, EquippedItemSerializer,
    PurchaseRequestSerializer, EquipRequestSerializer
)
from .selectors import WalletSelector, CatalogSelector, ShopSelector, InventorySelector, EquipmentSelector
from .services import PurchaseService, EquipmentService

class WalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: WalletSerializer})
    def get(self, request):
        wallet = WalletSelector.get_wallet(request.user)
        if not wallet:
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": WalletSerializer(wallet).data})

class WalletTransactionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: WalletTransactionSerializer(many=True)})
    def get(self, request):
        transactions = WalletSelector.get_transactions(request.user)
        return Response({"success": True, "data": WalletTransactionSerializer(transactions, many=True).data})

class CatalogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CatalogItemSerializer(many=True)})
    def get(self, request):
        items = CatalogSelector.get_items()
        return Response({"success": True, "data": CatalogItemSerializer(items, many=True).data})

class CatalogDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CatalogItemSerializer})
    def get(self, request, pk):
        item = CatalogSelector.get_item(pk)
        if not item:
            return Response({"success": False, "message": "Item not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": CatalogItemSerializer(item).data})

class BundleListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CatalogBundleSerializer(many=True)})
    def get(self, request):
        bundles = CatalogSelector.get_bundles()
        return Response({"success": True, "data": CatalogBundleSerializer(bundles, many=True).data})

class ShopFeaturedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CatalogItemSerializer(many=True)})
    def get(self, request):
        items = ShopSelector.get_featured_items()
        return Response({"success": True, "data": CatalogItemSerializer(items, many=True).data})

class ShopPurchaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PurchaseRequestSerializer, responses={200: dict})
    def post(self, request):
        serializer = PurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, msg = PurchaseService.purchase_item(request.user, str(serializer.validated_data['item_id']))
        return Response(
            {"success": success, "message": msg}, 
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        )

class InventoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: InventoryItemSerializer(many=True)})
    def get(self, request):
        inventory = InventorySelector.get_inventory(request.user)
        return Response({"success": True, "data": InventoryItemSerializer(inventory, many=True).data})

class EquipmentEquipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=EquipRequestSerializer, responses={200: dict})
    def patch(self, request):
        serializer = EquipRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, msg = EquipmentService.equip(request.user, str(serializer.validated_data['item_id']))
        return Response(
            {"success": success, "message": msg}, 
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        )

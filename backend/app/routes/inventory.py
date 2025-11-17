"""
================================================================================
Farm Management System - Inventory Module Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial inventory endpoints
  - Item master CRUD
  - Supplier and category management
  - Stock operations (add, use with FIFO)
  - Purchase order management
  - Transaction history
  - Low stock and expiry alerts
  - Dashboard summary

================================================================================
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.schemas.inventory import *
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_module_access
from app.services import inventory_service

router = APIRouter()


# ============================================================================
# ITEM MASTER ENDPOINTS
# ============================================================================


@router.get(
    "/items",
    response_model=ItemsListResponse,
    summary="List Items",
    description="Get paginated list of inventory items",
)
async def list_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """List all inventory items"""
    result = await inventory_service.get_items_list(
        category=category, is_active=is_active, page=page, limit=limit
    )
    return result


@router.post(
    "/items",
    response_model=ItemMasterItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create Item",
    description="Create new inventory item",
)
async def create_item(
    request: CreateItemRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Create new item"""
    item = await inventory_service.create_item(request, user.id)
    return item


@router.put(
    "/items/{item_id}",
    response_model=ItemMasterItem,
    summary="Update Item",
    description="Update inventory item",
)
async def update_item(
    item_id: int,
    request: UpdateItemRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Update item"""
    item = await inventory_service.update_item(item_id, request, user.id)
    return item


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Item",
    description="Delete/deactivate inventory item",
)
async def delete_item(
    item_id: int,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Delete item (soft delete)"""
    await inventory_service.delete_item(item_id)


# ============================================================================
# SUPPLIER ENDPOINTS
# ============================================================================


@router.get(
    "/suppliers",
    response_model=SuppliersListResponse,
    summary="List Suppliers",
    description="Get all suppliers",
)
async def list_suppliers(
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """List all suppliers"""
    suppliers = await inventory_service.get_suppliers_list()
    return {"suppliers": suppliers}


@router.post(
    "/suppliers",
    response_model=SupplierItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create Supplier",
    description="Create new supplier",
)
async def create_supplier(
    request: CreateSupplierRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Create new supplier"""
    supplier = await inventory_service.create_supplier(request)
    return supplier


@router.put(
    "/suppliers/{supplier_id}",
    response_model=SupplierItem,
    summary="Update Supplier",
    description="Update supplier",
)
async def update_supplier(
    supplier_id: int,
    request: UpdateSupplierRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Update supplier"""
    supplier = await inventory_service.update_supplier(supplier_id, request)
    return supplier


# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================


@router.get(
    "/categories",
    response_model=CategoriesListResponse,
    summary="List Categories",
    description="Get all inventory categories",
)
async def list_categories(
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """List all categories"""
    categories = await inventory_service.get_categories_list()
    return {"categories": categories}


# ============================================================================
# STOCK OPERATIONS
# ============================================================================


@router.post(
    "/stock/add",
    response_model=AddStockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Stock",
    description="Add stock batch to inventory",
)
async def add_stock(
    request: AddStockRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Add stock batch"""
    result = await inventory_service.add_stock(request, user.id)
    return result


@router.post(
    "/stock/use",
    response_model=UseStockResponse,
    summary="Use Stock (FIFO)",
    description="Deduct stock using FIFO logic",
)
async def use_stock(
    request: UseStockRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Use/deduct stock with FIFO"""
    result = await inventory_service.use_stock_fifo(
        request, user.id, user.full_name
    )
    return result


# ============================================================================
# PURCHASE ORDER ENDPOINTS
# ============================================================================


@router.get(
    "/purchase-orders",
    response_model=POsListResponse,
    summary="List Purchase Orders",
    description="Get paginated list of purchase orders (OPTIMIZED)",
)
async def list_purchase_orders(
    status: Optional[str] = Query("All", description="Filter by status"),
    days_back: int = Query(30, ge=1, le=365, description="Days back to fetch"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """
    List purchase orders (CRITICAL ENDPOINT - optimized for <200ms).
    This was the slow endpoint in Streamlit (2-3s), now target <200ms.
    """
    result = await inventory_service.get_purchase_orders_list(
        status=status if status != "All" else None,
        days_back=days_back,
        page=page,
        page_size=page_size,
    )
    return result


@router.post(
    "/purchase-orders",
    status_code=status.HTTP_201_CREATED,
    summary="Create Purchase Order",
    description="Create new purchase order with multiple items",
)
async def create_purchase_order(
    request: CreatePORequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Create purchase order"""
    po = await inventory_service.create_purchase_order(request, user.id)
    return po


@router.put(
    "/purchase-orders/{po_id}",
    summary="Update Purchase Order",
    description="Update purchase order status/details",
)
async def update_purchase_order(
    po_id: int,
    request: UpdatePORequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Update purchase order"""
    po = await inventory_service.update_purchase_order_status(po_id, request)
    return po


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================


@router.get(
    "/alerts/low-stock",
    response_model=LowStockAlertsResponse,
    summary="Low Stock Alerts",
    description="Get items with low stock levels",
)
async def get_low_stock_alerts(
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get low stock alerts"""
    items = await inventory_service.get_low_stock_alerts()
    return {"items": items, "total": len(items)}


@router.get(
    "/alerts/expiry",
    response_model=ExpiryAlertsResponse,
    summary="Expiry Alerts",
    description="Get items expiring soon",
)
async def get_expiry_alerts(
    days: int = Query(30, ge=1, le=365, description="Days to look ahead"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get expiry alerts"""
    items = await inventory_service.get_expiry_alerts(days=days)
    return {"items": items, "total": len(items)}


# ============================================================================
# TRANSACTION ENDPOINTS
# ============================================================================


@router.get(
    "/transactions",
    response_model=TransactionsListResponse,
    summary="Transaction History",
    description="Get inventory transaction history",
)
async def get_transactions(
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    days_back: int = Query(30, ge=1, le=365, description="Days back to fetch"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get transaction history"""
    result = await inventory_service.get_transactions_list(
        item_id=item_id, days_back=days_back, page=page, limit=limit
    )
    return result


# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================


@router.get(
    "/dashboard",
    response_model=InventoryDashboardResponse,
    summary="Inventory Dashboard",
    description="Get inventory dashboard summary",
)
async def get_inventory_dashboard(
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get inventory dashboard statistics"""
    stats = await inventory_service.get_inventory_dashboard()
    return stats

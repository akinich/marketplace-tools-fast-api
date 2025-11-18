"""
================================================================================
Farm Management System - Inventory Module Routes
================================================================================
Version: 1.2.0
Last Updated: 2025-11-18

Changelog:
----------
v1.2.0 (2025-11-18):
  - Added batch deduction endpoint (POST /stock/use-batch)
  - Added bulk fetch endpoint (POST /items/bulk-fetch)
  - Added stock reservation endpoints (reserve, list, cancel, confirm)
  - Enhanced cross-module integration for biofloc

v1.1.0 (2025-11-18):
  - Added DELETE endpoint for suppliers (soft delete)
  - Added POST/PUT/DELETE endpoints for categories (full CRUD)
  - Added stock adjustments endpoints (POST create, GET list)
  - Enhanced inventory management capabilities

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

from fastapi import APIRouter, Depends, Query, status, Path
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


@router.delete(
    "/suppliers/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Supplier",
    description="Delete/deactivate supplier",
)
async def delete_supplier(
    supplier_id: int,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Delete supplier (soft delete)"""
    await inventory_service.delete_supplier(supplier_id)


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


@router.post(
    "/categories",
    response_model=CategoryItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category",
    description="Create new inventory category",
)
async def create_category(
    request: CreateCategoryRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Create new category"""
    category = await inventory_service.create_category(request)
    return category


@router.put(
    "/categories/{category_id}",
    response_model=CategoryItem,
    summary="Update Category",
    description="Update inventory category",
)
async def update_category(
    category_id: int,
    request: UpdateCategoryRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Update category"""
    category = await inventory_service.update_category(category_id, request)
    return category


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Category",
    description="Delete inventory category",
)
async def delete_category(
    category_id: int,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Delete category"""
    await inventory_service.delete_category(category_id)


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
# STOCK ADJUSTMENTS
# ============================================================================


@router.post(
    "/stock/adjust",
    status_code=status.HTTP_201_CREATED,
    summary="Create Stock Adjustment",
    description="Create manual stock adjustment (increase, decrease, or recount)",
)
async def create_stock_adjustment(
    request: CreateAdjustmentRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Create stock adjustment"""
    result = await inventory_service.create_stock_adjustment(request, user.id)
    return result


@router.get(
    "/stock/adjustments",
    response_model=AdjustmentsListResponse,
    summary="List Stock Adjustments",
    description="Get stock adjustment history",
)
async def list_stock_adjustments(
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    days_back: int = Query(30, ge=1, le=365, description="Days back to fetch"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get stock adjustment history"""
    result = await inventory_service.get_stock_adjustments_list(
        item_id=item_id, days_back=days_back, page=page, limit=limit
    )
    return result


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


# ============================================================================
# BATCH DEDUCTION ENDPOINT
# ============================================================================


@router.post(
    "/stock/use-batch",
    response_model=BatchDeductionResponse,
    summary="Batch Deduct Stock",
    description="Deduct multiple items in a single atomic transaction (all succeed or all fail)",
)
async def batch_deduct_stock(
    request: BatchDeductionRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """
    Batch deduct multiple items atomically.
    Perfect for feeding sessions or multi-item operations.
    """
    result = await inventory_service.batch_deduct_stock(request, user.id, user.full_name)
    return result


# ============================================================================
# BULK FETCH ENDPOINT
# ============================================================================


@router.post(
    "/items/bulk-fetch",
    response_model=BulkFetchResponse,
    summary="Bulk Fetch Items",
    description="Fetch multiple items by IDs or SKUs in a single request",
)
async def bulk_fetch_items(
    request: BulkFetchRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """
    Fetch multiple items at once.
    Useful for morning stock checks or pre-operation validation.
    """
    result = await inventory_service.bulk_fetch_items(request)
    return result


# ============================================================================
# STOCK RESERVATION ENDPOINTS
# ============================================================================


@router.post(
    "/stock/reserve",
    response_model=ReservationItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stock Reservation",
    description="Reserve stock for planned usage (soft lock)",
)
async def create_reservation(
    request: CreateReservationRequest,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Create stock reservation for planned operations"""
    reservation = await inventory_service.create_reservation(request, user.id)
    return reservation


@router.get(
    "/stock/reservations",
    response_model=ReservationsListResponse,
    summary="List Stock Reservations",
    description="Get list of stock reservations with optional filters",
)
async def list_reservations(
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    module_reference: Optional[str] = Query(None, description="Filter by module"),
    status: Optional[str] = Query(None, description="Filter by status (pending, confirmed, cancelled, expired)"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """List stock reservations"""
    result = await inventory_service.get_reservations_list(
        item_id=item_id,
        module_reference=module_reference,
        status_filter=status,
    )
    return result


@router.delete(
    "/stock/reserve/{reservation_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel Reservation",
    description="Cancel a pending stock reservation",
)
async def cancel_reservation(
    reservation_id: str = Path(..., description="Reservation ID to cancel"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Cancel a pending reservation"""
    result = await inventory_service.cancel_reservation(reservation_id)
    return result


@router.post(
    "/stock/confirm-reservation/{reservation_id}",
    response_model=ConfirmReservationResponse,
    summary="Confirm Reservation",
    description="Convert reservation to actual stock usage (FIFO deduction)",
)
async def confirm_reservation(
    reservation_id: str = Path(..., description="Reservation ID to confirm"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Confirm reservation and deduct stock"""
    result = await inventory_service.confirm_reservation(
        reservation_id, user.id, user.full_name
    )
    return result


# ============================================================================
# MODULE-SPECIFIC ENDPOINTS
# ============================================================================


@router.get(
    "/module/{module_name}/items",
    summary="Get Module Items",
    description="Get items used by a specific module",
)
async def get_module_items(
    module_name: str = Path(..., description="Module name (biofloc, hatchery, etc.)"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get items used by a specific module"""
    result = await inventory_service.get_module_items(module_name)
    return result


@router.get(
    "/module/{module_name}/consumption",
    response_model=ModuleConsumptionResponse,
    summary="Get Module Consumption",
    description="Get consumption report for a specific module",
)
async def get_module_consumption(
    module_name: str = Path(..., description="Module name"),
    days_back: int = Query(30, ge=1, le=365, description="Days back to analyze"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get consumption report for a module"""
    result = await inventory_service.get_module_consumption(module_name, days_back)
    return result


# ============================================================================
# ITEM-MODULE MAPPING ENDPOINTS
# ============================================================================


@router.post(
    "/items/{item_id}/modules",
    response_model=ItemModuleMappingItem,
    status_code=status.HTTP_201_CREATED,
    summary="Map Item to Module",
    description="Create a mapping between an item and a module",
)
async def create_item_module_mapping(
    item_id: int = Path(..., description="Item ID"),
    request: CreateItemModuleMappingRequest = ...,
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Map an item to a module"""
    mapping = await inventory_service.create_item_module_mapping(item_id, request)
    return mapping


@router.get(
    "/items/{item_id}/modules",
    response_model=ItemModuleMappingsResponse,
    summary="Get Item Module Mappings",
    description="Get all module mappings for an item",
)
async def get_item_module_mappings(
    item_id: int = Path(..., description="Item ID"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Get module mappings for an item"""
    result = await inventory_service.get_item_module_mappings(item_id)
    return result


@router.delete(
    "/items/{item_id}/modules/{module_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Module Mapping",
    description="Remove a module mapping from an item",
)
async def delete_item_module_mapping(
    item_id: int = Path(..., description="Item ID"),
    module_name: str = Path(..., description="Module name to unmap"),
    user: CurrentUser = Depends(require_module_access("inventory")),
):
    """Remove module mapping from item"""
    await inventory_service.delete_item_module_mapping(item_id, module_name)

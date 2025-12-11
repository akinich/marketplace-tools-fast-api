"""
================================================================================
Marketplace ERP - Customer Price List Routes
================================================================================
Version: 1.0.0
Created: 2025-12-11

API endpoints for customer price list management, items, Excel import/export,
and price resolution.
================================================================================
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import date
from decimal import Decimal
import io

from app.schemas.price_list import (
    PriceListCreate, PriceListUpdate, PriceListResponse, PriceListListResponse,
    PriceListItemCreate, PriceListItemResponse, PriceListItemsResponse,
    BulkPriceListItemCreate, ExcelImportResponse, DuplicatePriceListRequest,
    ResolvedPriceResponse, PriceHistoryResponse, AssignedCustomersResponse,
    PriceListStatsResponse
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import price_list_service

router = APIRouter()


# ============================================================================
# PRICE LIST MANAGEMENT
# ============================================================================

@router.get(
    "",
    response_model=PriceListListResponse,
    summary="List Price Lists",
    description="Get all price lists with optional filters"
)
async def list_price_lists(
    status_filter: Optional[str] = Query(None, description="Filter by status: active, expired, upcoming"),
    date_filter: Optional[date] = Query(None, description="Get lists active on specific date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all price lists with optional filters
    
    - **status_filter**: active, expired, or upcoming
    - **date_filter**: Get lists valid for specific date
    - **page**: Page number (default: 1)
    - **limit**: Results per page (default: 50)
    """
    result = await price_list_service.get_price_lists(
        status_filter=status_filter,
        date_filter=date_filter,
        page=page,
        limit=limit
    )
    return result


@router.post(
    "",
    response_model=PriceListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Price List",
    description="Create new customer price list"
)
async def create_price_list(
    data: PriceListCreate,
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create new price list
    
    - **price_list_name**: Unique name (required)
    - **valid_from**: Start date (required)
    - **valid_to**: End date (optional, NULL = indefinite)
    - **is_active**: Enable/disable (default: true)
    """
    result = await price_list_service.create_price_list(
        data.dict(),
        current_user.id
    )
    return result


@router.get(
    "/{price_list_id}",
    response_model=PriceListResponse,
    summary="Get Price List",
    description="Get price list details by ID"
)
async def get_price_list(
    price_list_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get single price list by ID"""
    result = await price_list_service.get_price_list_by_id(price_list_id)
    return result


@router.put(
    "/{price_list_id}",
    response_model=PriceListResponse,
    summary="Update Price List",
    description="Update price list metadata"
)
async def update_price_list(
    price_list_id: int,
    data: PriceListUpdate,
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Update price list
    
    All fields optional - only send fields to update
    """
    result = await price_list_service.update_price_list(
        price_list_id,
        data.dict(exclude_unset=True),
        current_user.id
    )
    return result


@router.delete(
    "/{price_list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Price List",
    description="Delete price list (validates no customers assigned)"
)
async def delete_price_list(
    price_list_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Delete price list
    
    - Will fail if customers are assigned
    - Cascades to items and history
    """
    await price_list_service.delete_price_list(price_list_id)
    return None


@router.post(
    "/{price_list_id}/duplicate",
    response_model=PriceListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate Price List",
    description="Create copy of price list with optional items"
)
async def duplicate_price_list(
    price_list_id: int,
    data: DuplicatePriceListRequest,
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Duplicate price list
    
    - **new_name**: Name for duplicated list (required)
    - **copy_items**: Copy all items (default: true)
    - **valid_from**: New valid from date (optional)
    - **valid_to**: New valid to date (optional)
    """
    result = await price_list_service.duplicate_price_list(
        price_list_id,
        data.new_name,
        data.copy_items,
        data.valid_from,
        data.valid_to,
        current_user.id
    )
    return result


# ============================================================================
# PRICE LIST ITEMS
# ============================================================================

@router.get(
    "/{price_list_id}/items",
    response_model=PriceListItemsResponse,
    summary="Get Price List Items",
    description="Get all items in a price list"
)
async def get_price_list_items(
    price_list_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all items with prices in this price list"""
    result = await price_list_service.get_price_list_items(price_list_id)
    return result


@router.post(
    "/{price_list_id}/items",
    response_model=PriceListItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add/Update Item",
    description="Add or update single item in price list"
)
async def add_or_update_item(
    price_list_id: int,
    data: PriceListItemCreate,
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Add or update item price
    
    - Upserts: Creates if doesn't exist, updates if exists
    - **item_id**: Item to add/update
    - **price**: Price in INR (must be > 0)
    - **notes**: Optional notes
    """
    result = await price_list_service.add_or_update_price_list_item(
        price_list_id,
        data.item_id,
        data.price,
        data.notes
    )
    return result


@router.post(
    "/{price_list_id}/items/bulk",
    summary="Bulk Add/Update Items",
    description="Bulk add or update multiple items"
)
async def bulk_add_or_update_items(
    price_list_id: int,
    data: BulkPriceListItemCreate,
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Bulk add or update items
    
    - Accepts array of items
    - Returns count of added, updated, and errors
    """
    result = await price_list_service.bulk_add_or_update_items(
        price_list_id,
        [item.dict() for item in data.items]
    )
    return result


@router.put(
    "/{price_list_id}/items/{item_id}",
    response_model=PriceListItemResponse,
    summary="Update Item Price",
    description="Update specific item price"
)
async def update_item_price(
    price_list_id: int,
    item_id: int,
    data: PriceListItemCreate,
    current_user: CurrentUser = Depends(require_admin)
):
    """Update price for specific item"""
    result = await price_list_service.add_or_update_price_list_item(
        price_list_id,
        item_id,
        data.price,
        data.notes
    )
    return result


@router.delete(
    "/{price_list_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Item",
    description="Remove item from price list"
)
async def delete_item(
    price_list_id: int,
    item_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """Remove item from price list"""
    await price_list_service.delete_price_list_item(price_list_id, item_id)
    return None


# ============================================================================
# EXCEL IMPORT/EXPORT
# ============================================================================

@router.get(
    "/template/download",
    summary="Download Excel Template",
    description="Download Excel template for bulk import"
)
async def download_template(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Download Excel template for price list import
    
    Template includes:
    - SKU column
    - Item Name (read-only reference)
    - Price column
    - Notes column
    """
    excel_bytes = await price_list_service.generate_excel_template()
    
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=price_list_template.xlsx"}
    )


@router.post(
    "/{price_list_id}/import",
    response_model=ExcelImportResponse,
    summary="Import from Excel",
    description="Import price list items from Excel file"
)
async def import_from_excel(
    price_list_id: int,
    file: UploadFile = File(..., description="Excel file with price list items"),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Import items from Excel
    
    - Excel file must match template format
    - SKUs must exist in items database
    - Prices must be > 0
    - Returns import summary with errors
    """
    result = await price_list_service.import_from_excel(price_list_id, file)
    return result


@router.get(
    "/{price_list_id}/export",
    summary="Export to Excel",
    description="Export price list items to Excel"
)
async def export_to_excel(
    price_list_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Export all items in price list to Excel file"""
    excel_bytes = await price_list_service.export_to_excel(price_list_id)
    
    # Get price list name for filename
    price_list = await price_list_service.get_price_list_by_id(price_list_id)
    safe_name = price_list['price_list_name'].replace(' ', '_').replace('/', '_')
    filename = f"price_list_{safe_name}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# CUSTOMER ASSIGNMENT
# ============================================================================

@router.get(
    "/{price_list_id}/customers",
    response_model=AssignedCustomersResponse,
    summary="Get Assigned Customers",
    description="Get all customers assigned to this price list"
)
async def get_assigned_customers(
    price_list_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all customers using this price list"""
    result = await price_list_service.get_assigned_customers(price_list_id)
    return result


# ============================================================================
# PRICE RESOLUTION
# ============================================================================

@router.get(
    "/resolve-price/customer/{customer_id}/item/{item_id}",
    response_model=ResolvedPriceResponse,
    summary="Resolve Price",
    description="Get resolved price for customer + item combination"
)
async def resolve_price(
    customer_id: int,
    item_id: int,
    date_for: Optional[date] = Query(None, description="Date to resolve price for (default: today)"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Resolve price for customer + item
    
    Resolution priority:
    1. Valid price list price (if customer has price list assigned and it's active for date)
    2. Zoho default price (from zoho_items.rate)
    
    Returns:
    - Resolved price
    - Source (price_list or zoho_default)
    - Price list info if applicable
    """
    result = await price_list_service.resolve_customer_item_price(
        customer_id,
        item_id,
        date_for
    )
    return result


# ============================================================================
# PRICE HISTORY
# ============================================================================

@router.get(
    "/{price_list_id}/history",
    response_model=PriceHistoryResponse,
    summary="Get Change History",
    description="Get audit log of all changes to price list"
)
async def get_history(
    price_list_id: int,
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get change history
    
    Shows all changes to:
    - Price list metadata (name, dates, active status)
    - Individual item prices
    """
    result = await price_list_service.get_price_list_history(price_list_id, limit)
    return result


# ============================================================================
# STATISTICS
# ============================================================================

@router.get(
    "/stats/summary",
    response_model=PriceListStatsResponse,
    summary="Get Statistics",
    description="Get price list statistics and counts"
)
async def get_stats(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get statistics
    
    Returns:
    - Total price lists
    - Active/expired/upcoming counts
    - Customers with price lists
    - Lists expiring soon
    """
    result = await price_list_service.get_price_list_stats()
    return result

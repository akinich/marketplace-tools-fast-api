"""
================================================================================
Zoho Item Management API Routes
================================================================================
Version: 1.0.0
Created: 2025-12-02

API endpoints for Zoho Item Master module
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.zoho_item import (
    ZohoItemUpdate,
    ZohoItemResponse,
    ZohoItemListResponse,
    ZohoSyncRequest,
    ZohoSyncResponse,
    ZohoItemStatsResponse
)
from app.services import zoho_item_service

router = APIRouter()


# ============================================================================
# ZOHO ITEM CRUD ENDPOINTS
# ============================================================================

@router.get("/zoho-items", response_model=ZohoItemListResponse)
async def list_zoho_items(
    search: Optional[str] = Query(None, description="Search by item name, SKU, or HSN/SAC"),
    active_only: bool = Query(True, description="Filter active items only"),
    item_type: Optional[str] = Query(None, description="Filter by item_type"),
    product_type: Optional[str] = Query(None, description="Filter by product_type: goods, service"),
    limit: int = Query(1000, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List Zoho items with optional search and filters

    Requires: Any authenticated user
    """
    items, total_count = await zoho_item_service.get_items(
        search=search,
        active_only=active_only,
        item_type=item_type,
        product_type=product_type,
        limit=limit,
        offset=offset
    )

    return {
        "items": items,
        "total": total_count
    }


# ============================================================================
# ZOHO BOOKS SYNC ENDPOINTS
# ============================================================================

@router.post("/zoho-items/sync", response_model=ZohoSyncResponse)
async def sync_zoho_items(
    sync_request: ZohoSyncRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Sync items from Zoho Books API

    Requires: Admin role
    """
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can sync Zoho items"
        )

    result = await zoho_item_service.sync_from_zoho_books(
        synced_by=current_user.id,
        force_refresh=sync_request.force_refresh
    )

    message = f"Sync completed: {result['added']} added"
    if result['updated'] > 0:
        message += f", {result['updated']} updated"
    if result['skipped'] > 0:
        message += f", {result['skipped']} skipped"
    if result['errors'] > 0:
        message += f", {result['errors']} errors"

    return {
        **result,
        "message": message
    }


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/zoho-items/stats", response_model=ZohoItemStatsResponse)
async def get_zoho_item_stats(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get Zoho item statistics

    Requires: Any authenticated user
    """
    stats = await zoho_item_service.get_item_stats()
    return stats


# ============================================================================
# ZOHO ITEM DETAIL ENDPOINTS (Must come after specific routes like /sync, /stats)
# ============================================================================

@router.get("/zoho-items/{item_id}", response_model=ZohoItemResponse)
async def get_zoho_item(
    item_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a single Zoho item by ID

    Requires: Any authenticated user
    """
    item = await zoho_item_service.get_item_by_id(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zoho item not found"
        )

    return item


@router.patch("/zoho-items/{item_id}", response_model=ZohoItemResponse)
async def update_zoho_item(
    item_id: int,
    item_data: ZohoItemUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a Zoho item
    
    Note: Zoho Books is the source of truth. Updates are limited.
    Admins: Can edit fields (use with caution - will be overwritten on next sync)
    Users: Read-only access
    """
    is_admin = current_user.role == "Admin"

    item = await zoho_item_service.update_item(
        item_id,
        item_data,
        updated_by=current_user.id,
        is_admin=is_admin
    )

    return item

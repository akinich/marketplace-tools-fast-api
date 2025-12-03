"""
================================================================================
WooCommerce Customer Management API Routes
================================================================================
Version: 1.0.0
Created: 2025-12-03

API endpoints for WooCommerce Customer Master module
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.woo_customer import (
    WooCustomerUpdate,
    WooCustomerResponse,
    WooCustomerListResponse,
    WooCustomerSyncRequest,
    WooCustomerSyncResponse,
    WooCustomerStatsResponse
)
from app.services import woo_customer_service

router = APIRouter()


# ============================================================================
# CUSTOMER CRUD ENDPOINTS
# ============================================================================

@router.get("/woo-customers", response_model=WooCustomerListResponse)
async def list_woo_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    paying_only: bool = Query(False, description="Filter paying customers only"),
    limit: int = Query(1000, ge=1, le=10000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List WooCommerce customers with optional search and filters

    Requires: Any authenticated user
    """
    customers, total_count = await woo_customer_service.get_customers(
        search=search,
        paying_only=paying_only,
        limit=limit,
        offset=offset
    )

    return {
        "customers": customers,
        "total": total_count
    }


# ============================================================================
# SYNC ENDPOINTS
# ============================================================================

@router.post("/woo-customers/sync")
async def sync_woo_customers(
    sync_request: WooCustomerSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Start WooCommerce customer sync in background

    Requires: Admin role
    Returns immediately, use /sync-progress to track progress
    """
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can sync WooCommerce customers"
        )

    # Check if sync is already in progress
    current_progress = await woo_customer_service.get_sync_progress()
    if current_progress["in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sync already in progress. Please wait for it to complete."
        )

    # Start sync in background
    background_tasks.add_task(
        woo_customer_service.sync_from_woocommerce,
        synced_by=current_user.id
    )

    return {
        "message": "Sync started in background. Use /sync-progress to track progress.",
        "in_progress": True
    }


@router.get("/woo-customers/sync-progress")
async def get_sync_progress(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current sync progress

    Requires: Any authenticated user
    Returns progress percentage, ETA, and counts
    """
    progress = await woo_customer_service.get_sync_progress()
    return progress


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/woo-customers/stats", response_model=WooCustomerStatsResponse)
async def get_woo_customer_stats(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get WooCommerce customer statistics

    Requires: Any authenticated user
    """
    stats = await woo_customer_service.get_customer_stats()
    return stats


# ============================================================================
# CUSTOMER DETAIL ENDPOINTS (Must come after specific routes like /sync, /stats)
# ============================================================================

@router.get("/woo-customers/{customer_id}", response_model=WooCustomerResponse)
async def get_woo_customer(
    customer_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a single WooCommerce customer by ID

    Requires: Any authenticated user
    """
    customer = await woo_customer_service.get_customer_by_id(customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.patch("/woo-customers/{customer_id}", response_model=WooCustomerResponse)
async def update_woo_customer(
    customer_id: int,
    customer_data: WooCustomerUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a WooCommerce customer
    
    Note: WooCommerce is the source of truth. Updates are limited.
    Admins: Can edit fields (use with caution - will be overwritten on next sync)
    Users: Can only edit notes field
    """
    is_admin = current_user.role == "Admin"

    customer = await woo_customer_service.update_customer(
        customer_id,
        customer_data,
        updated_by=current_user.id,
        is_admin=is_admin
    )

    return customer

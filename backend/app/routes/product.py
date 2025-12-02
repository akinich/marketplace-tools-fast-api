"""
================================================================================
Product Management Routes
================================================================================
Version: 1.0.0
Created: 2025-12-01

API endpoints for B2C Item Master module
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    WooCommerceSyncRequest,
    WooCommerceSyncResponse,
    ProductStatsResponse
)
from app.services import product_service

router = APIRouter()


# ============================================================================
# PRODUCT CRUD ENDPOINTS
# ============================================================================

@router.get("/products", response_model=ProductListResponse)
async def list_products(
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    active_only: bool = Query(True, description="Filter active products only"),
    product_type: Optional[str] = Query(None, description="Filter by type: simple, variations"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List products with optional search and filters

    Requires: Any authenticated user
    """
    offset = (page - 1) * limit

    products = await product_service.get_products(
        search=search,
        active_only=active_only,
        product_type=product_type,
        limit=limit,
        offset=offset
    )

    # Get total count for pagination
    # For simplicity, using the returned count (could be optimized with separate count query)
    total = len(products)

    return {
        "products": products,
        "total": total,
        "page": page,
        "limit": limit
    }


# ============================================================================
# WOOCOMMERCE SYNC ENDPOINTS
# ============================================================================

@router.post("/products/sync", response_model=WooCommerceSyncResponse)
async def sync_products(
    sync_request: WooCommerceSyncRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Sync products from WooCommerce API

    Requires: Admin role
    """
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can sync products"
        )

    result = await product_service.sync_from_woocommerce(
        sync_request=sync_request,
        synced_by=current_user.id
    )

    message = f"Sync completed: {result['added']} added"
    if result['updated'] > 0:
        message += f", {result['updated']} updated"
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

@router.get("/products/stats", response_model=ProductStatsResponse)
async def get_product_stats(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get product statistics

    Requires: Any authenticated user
    """
    stats = await product_service.get_product_stats()
    return stats


# ============================================================================
# PRODUCT DETAIL ENDPOINTS (Must come after specific routes like /sync, /stats)
# ============================================================================

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a single product by ID

    Requires: Any authenticated user
    """
    product = await product_service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new product manually

    Requires: Admin role
    """
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create products"
        )

    product = await product_service.create_product(
        product_data,
        created_by=current_user.id
    )

    return product


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a product

    Admins: Can edit all fields
    Users: Can only edit HSN, Zoho Name, Usage Units, Notes
    """
    is_admin = current_user.role == "Admin"

    product = await product_service.update_product(
        product_id,
        product_data,
        updated_by=current_user.id,
        is_admin=is_admin
    )

    return product

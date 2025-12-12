"""
================================================================================
Marketplace ERP - Sales Order Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-12-07

Description:
  API endpoints for sales order management. Provides SO creation, updates,
  customer pricing management, and listing using fastapi routers.

Endpoints:
  POST   /api/v1/sales-orders/create             - Create new SO
  GET    /api/v1/sales-orders/{so_id}            - Get SO details
  PUT    /api/v1/sales-orders/{so_id}/update     - Update SO
  GET    /api/v1/sales-orders/list               - List SOs with filters
  POST   /api/v1/sales-orders/customer-pricing   - Manage pricing (admin)
  GET    /api/v1/sales-orders/pricing-history    - Get price history

================================================================================
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from datetime import date

from app.schemas.sales_orders import (
    SOCreateRequest, SOUpdateRequest, SODetailResponse,
    SOListResponse, CustomerPricingRequest, PriceHistoryResponse,
    ActivePriceResponse
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import sales_order_service

router = APIRouter()


# ============================================================================
# SO MANAGEMENT ROUTES
# ============================================================================

@router.get("/next-number")
async def get_next_so_number(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get next sequential SO number.
    Format: SO/YY-YY/XXXX
    """
    try:
        result = await sales_order_service.generate_so_number()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SO number: {str(e)}"
        )


@router.get("/list", response_model=SOListResponse)
async def list_sos(
    status: Optional[str] = Query(None, description="Filter by status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    from_date: Optional[date] = Query(None, description="Filter by order date from"),
    to_date: Optional[date] = Query(None, description="Filter by order date to"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List sales orders with filtering and pagination.
    """
    try:
        result = await sales_order_service.list_sos(
            status=status,
            customer_id=customer_id,
            from_date=from_date,
            to_date=to_date,
            item_id=item_id,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list SOs: {str(e)}"
        )


@router.post("/create", response_model=SODetailResponse, status_code=status.HTTP_201_CREATED)
async def create_so(
    request: SOCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create new sales order with 3-tier pricing logic.
    """
    try:
        result = await sales_order_service.create_so(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SO: {str(e)}"
        )



@router.get("/price-check")
async def check_price(
    customer_id: int = Query(..., description="Customer ID"),
    item_id: int = Query(..., description="Item ID"),
    order_date: date = Query(default_factory=date.today, description="Date for pricing"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Check 3-tier price for specific customer/item/date.
    """
    try:
        result = await sales_order_service.get_item_price(customer_id, item_id, order_date)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check price: {str(e)}"
        )


@router.get("/{so_id}", response_model=SODetailResponse)
async def get_so(
    so_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get complete SO details.
    """
    try:
        so = await sales_order_service.get_so_details(so_id)
        if not so:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SO {so_id} not found"
            )
        return so
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SO: {str(e)}"
        )


@router.put("/{so_id}/update", response_model=SODetailResponse)
async def update_so(
    so_id: int,
    request: SOUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update sales order.
    """
    try:
        result = await sales_order_service.update_so(so_id, request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update SO: {str(e)}"
        )


# ============================================================================
# CUSTOMER PRICING ROUTES (ADMIN ONLY)
# ============================================================================

@router.post("/customer-pricing", dependencies=[Depends(require_admin)])
async def manage_customer_pricing(
    request: CustomerPricingRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Add or update customer-item pricing (admin only).
    """
    try:
        result = await sales_order_service.manage_customer_pricing(request, str(current_user.id))
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage customer pricing: {str(e)}"
        )


@router.get("/customer-pricing/history", dependencies=[Depends(require_admin)])
async def get_price_history(
    customer_id: int = Query(..., description="Customer ID"),
    item_id: Optional[int] = Query(None, description="Optional item ID filter"),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get price history for customer-item combinations (admin only).
    """
    try:
        results = await sales_order_service.get_price_history(customer_id, item_id)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price history: {str(e)}"
        )

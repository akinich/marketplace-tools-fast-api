"""
================================================================================
Orders Routes - FastAPI Endpoints (Simplified)
================================================================================
Version: 3.0.0
Created: 2025-12-08

Description:
    API routes for B2C Orders module
    - Order listing with pagination
    - Single order view
    - Manual sync from WooCommerce (with date range support)

Endpoints:
    GET    /orders           - List orders with filtering & pagination
    GET    /orders/{id}      - Get single order by ID
    POST   /orders/sync      - Manual sync from WooCommerce API

Authentication:
    - All endpoints require valid JWT token

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import Optional
from datetime import datetime, date
import logging

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.orders import (
    OrderResponse,
    OrderListResponse,
    SyncOrdersRequest,
    SyncOrdersResponse,
)
from app.services.orders_service import OrdersService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Order Endpoints
# ============================================================================

@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List orders with filtering and pagination

    - **status**: Filter by order status (pending, processing, completed, etc.)
    - **customer_id**: Filter by customer ID
    - **start_date**: Filter orders from this date
    - **end_date**: Filter orders up to this date
    - **page**: Page number (starts at 1)
    - **limit**: Number of orders per page (max 100)
    """
    try:
        offset = (page - 1) * limit

        orders = await OrdersService.get_orders(
            status=status,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Get total count for pagination
        total = await OrdersService.count_orders(
            status=status,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )

        return OrderListResponse(
            orders=orders,
            total=total,
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Error listing orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get single order by ID

    Returns order details including line items
    """
    try:
        order = await OrdersService.get_order_by_id(order_id, include_items=True)

        if not order:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )

        return order

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order"
        )


# ============================================================================
# Sync Endpoint
# ============================================================================

@router.post("/sync", response_model=SyncOrdersResponse)
async def sync_orders(
    sync_request: SyncOrdersRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Manually trigger order sync from WooCommerce API

    - **start_date**: Start date (optional, defaults to 3 days ago)
    - **end_date**: End date (optional, defaults to today)

    This will fetch orders from WooCommerce API and save them to database.
    """
    try:
        logger.info(f"Manual sync triggered by user {current_user.id}: {sync_request.start_date} to {sync_request.end_date}")

        # Perform sync
        result = await OrdersService.sync_orders_from_woocommerce(
            start_date=sync_request.start_date,
            end_date=sync_request.end_date
        )

        logger.info(f"Sync completed: {result.synced} orders synced")
        logger.info(f"Result object: {result}")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result dict: {result.model_dump()}")

        return result

    except Exception as e:
        logger.error(f"Error during manual sync: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync orders: {str(e)}"
        )


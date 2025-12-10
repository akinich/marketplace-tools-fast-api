"""
================================================================================
B2C Orders Routes - FastAPI Endpoints
================================================================================
Version: 1.0.0
Created: 2025-12-09

Description:
    API routes for B2C Orders module
    - Get orders from database (with pagination)
    - Save WooCommerce orders to database
    - Get single order details

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
import logging

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.b2c_orders import (
    OrderListResponse,
    OrderResponse,
    SaveOrdersRequest,
    SaveOrdersResponse
)
from app.services.b2c_orders_service import B2COrdersService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")  # Removed response_model temporarily to debug
async def list_orders(
    order_status: Optional[str] = Query(None, description="Filter by order status", alias="status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get orders from database with pagination and filtering
    
    - **status**: Filter by order status (pending, processing, completed, etc.)
    - **page**: Page number (starts at 1)
    - **limit**: Number of orders per page (max 100)
    """
    try:
        offset = (page - 1) * limit
        
        orders = await B2COrdersService.get_orders(
            status=order_status,
            limit=limit,
            offset=offset
        )
        
        total = await B2COrdersService.count_orders(status=order_status)
        
        # Return raw dict to bypass Pydantic validation
        return {
            "orders": orders,
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch orders: {str(e)}"  # Include actual error
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get single order by ID with line items"""
    try:
        order = await B2COrdersService.get_order_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order"
        )


@router.post("/save", response_model=SaveOrdersResponse)
async def save_orders(
    request: SaveOrdersRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Save WooCommerce orders to database
    
    This endpoint receives orders from the frontend (fetched via WooCommerce API)
    and saves them to the database with UPSERT logic.
    """
    try:
        logger.info(f"Saving {len(request.orders)} orders to database")
        
        result = await B2COrdersService.save_orders_batch(request.orders)
        
        logger.info(f"Save completed: {result['created']} created, {result['updated']} updated, {result['errors']} errors")
        
        return SaveOrdersResponse(**result)
        
    except Exception as e:
        logger.error(f"Error saving orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save orders: {str(e)}"
        )

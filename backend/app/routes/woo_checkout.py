"""
================================================================================
WooCommerce Checkout Routes - FastAPI Endpoints
================================================================================
Version: 1.0.0
Created: 2025-12-04

Description:
    API routes for WooCommerce checkout functionality
    - Place orders endpoint
    - Check customer mapping status

Endpoints:
    POST /woo-checkout/place-order - Create WooCommerce order
    GET /woo-checkout/customer-status - Check user's WooCommerce mapping

Authentication:
    - Requires valid JWT token
    - Requires 'order_place_test' module access

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging
import json

from app.auth.dependencies import get_current_user, require_module_access
from app.schemas.auth import CurrentUser
from app.schemas.woo_checkout import (
    CheckoutRequestSchema,
    WooOrderResponseSchema,
    CustomerStatusSchema
)
from app.services.woo_checkout_service import WooCheckoutService
from app.database import execute_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/woo-checkout", tags=["WooCommerce Checkout"])


# ============================================================================
# Checkout Endpoints
# ============================================================================

@router.post("/place-order", response_model=WooOrderResponseSchema)
async def place_order(
    request: CheckoutRequestSchema,
    current_user: CurrentUser = Depends(require_module_access("order_place_test"))
):
    """
    Place a WooCommerce order for the authenticated user
    
    - **line_items**: List of products with IDs and quantities
    
    Returns WooCommerce order details including order ID, status, and total
    """
    try:
        # Convert line items to dict format
        line_items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "variation_id": item.variation_id
            }
            for item in request.line_items
        ]
        
        # Create order via service
        order_data = await WooCheckoutService.create_order(
            user_id=current_user.id,
            line_items=line_items,
            wc_customer_id=request.wc_customer_id
        )
        
        # Log activity
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            current_user.id,
            'order_created',
            'order_place_test',
            f"Created WooCommerce order #{order_data['id']}",
            json.dumps({
                'wc_order_id': order_data['id'],
                'total': order_data.get('total'),
                'status': order_data.get('status'),
                'item_count': len(line_items)
            })
        )
        
        return order_data
        
    except ValueError as e:
        # User validation errors (no customer mapping)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}", exc_info=True)
        
        # Log error
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata, success)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            current_user.id,
            'module_error',
            'order_place_test',
            f"Failed to place order: {str(e)}",
            json.dumps({'error': str(e)}),
            False
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to place order. Please try again or contact support."
        )


@router.get("/customer-status", response_model=CustomerStatusSchema)
async def get_customer_status(
    current_user: CurrentUser = Depends(require_module_access("order_place_test"))
):
    """
    Check if the authenticated user has a WooCommerce customer mapping
    
    Returns status information about the user's WooCommerce customer association
    """
    try:
        status_info = await WooCheckoutService.check_customer_status(current_user.id)
        return status_info
        
    except Exception as e:
        logger.error(f"Error checking customer status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to check customer status"
        )

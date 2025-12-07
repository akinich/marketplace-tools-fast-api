"""
================================================================================
Marketplace ERP - Pricing Routes
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.pricing import CustomerPriceCreate, CustomerPriceResponse, PriceLookupResponse
from app.services import pricing_service
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/customer/{customer_id}/item/{item_id}", response_model=PriceLookupResponse)
async def get_price(
    customer_id: int, 
    item_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get price for a specific item and customer.
    """
    return await pricing_service.get_item_price(customer_id, item_id)

@router.get("/{customer_id}", response_model=List[dict])
async def get_customer_prices(
    customer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all custom prices for a customer.
    """
    return await pricing_service.get_customer_prices(customer_id)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def set_customer_price(
    data: CustomerPriceCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Set or update a custom price for a customer/item.
    """
    # Optional: Check if user is admin or allowed
    price_id = await pricing_service.set_customer_price(data)
    return {"id": price_id, "message": "Price updated successfully"}

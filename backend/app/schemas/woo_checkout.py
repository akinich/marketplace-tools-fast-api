"""
================================================================================
WooCommerce Checkout Schemas
================================================================================
Version: 1.0.0
Created: 2025-12-04

Description:
    Pydantic schemas for WooCommerce checkout functionality
    - Request/response models for order placement
    - Line item validation
    - WooCommerce order response mapping

================================================================================
"""

from typing import List, Optional
from pydantic import BaseModel, Field, conint


class LineItemSchema(BaseModel):
    """Line item for WooCommerce order"""
    product_id: conint(gt=0) = Field(..., description="WooCommerce product ID")
    quantity: conint(gt=0) = Field(..., description="Quantity to order")
    variation_id: Optional[int] = Field(None, description="Product variation ID (if applicable)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 123,
                "quantity": 2,
                "variation_id": 456
            }
        }


class CheckoutRequestSchema(BaseModel):
    """Request schema for placing WooCommerce order"""
    line_items: List[LineItemSchema] = Field(..., min_length=1, description="List of items to order")
    wc_customer_id: Optional[int] = Field(None, description="WooCommerce customer ID (optional override)")

    class Config:
        json_schema_extra = {
            "example": {
                "line_items": [
                    {"product_id": 123, "quantity": 2},
                    {"product_id": 456, "quantity": 1, "variation_id": 789}
                ],
                "wc_customer_id": 42
            }
        }


class WooOrderResponseSchema(BaseModel):
    """WooCommerce order response"""
    id: int = Field(..., description="WooCommerce order ID")
    status: str = Field(..., description="Order status (e.g., pending, processing)")
    total: str = Field(..., description="Order total amount")
    currency: Optional[str] = Field(None, description="Currency code")
    date_created: Optional[str] = Field(None, description="Order creation date")
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_method_title: Optional[str] = Field(None, description="Payment method title")

    class Config:
        extra = "allow"  # Allow additional WooCommerce fields
        json_schema_extra = {
            "example": {
                "id": 12345,
                "status": "pending",
                "total": "99.99",
                "currency": "USD",
                "date_created": "2025-12-04T01:00:00",
                "payment_method": "cod",
                "payment_method_title": "Cash on Delivery"
            }
        }


class CustomerStatusSchema(BaseModel):
    """Customer WooCommerce mapping status"""
    has_wc_customer_id: bool = Field(..., description="Whether user has WooCommerce customer ID")
    wc_customer_id: Optional[int] = Field(None, description="WooCommerce customer ID if exists")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "has_wc_customer_id": True,
                "wc_customer_id": 789,
                "message": "User is mapped to WooCommerce customer"
            }
        }

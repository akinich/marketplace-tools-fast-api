"""
================================================================================
B2C Orders Schemas - Pydantic Models
================================================================================
Version: 1.0.0
Created: 2025-12-09

Description:
    Pydantic schemas for B2C Orders module

================================================================================
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class OrderItemResponse(BaseModel):
    """Response schema for order items"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    name: str
    sku: Optional[str] = None
    quantity: int
    price: Decimal
    subtotal: Decimal
    total: Decimal
    tax: Decimal


class OrderResponse(BaseModel):
    """Response schema for orders"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    woo_order_id: int
    order_number: str
    customer_id: Optional[int] = None
    status: str
    date_created: datetime
    date_modified: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    date_paid: Optional[datetime] = None
    currency: str
    subtotal: Decimal
    total_tax: Decimal
    shipping_total: Decimal
    discount_total: Decimal
    total: Decimal
    payment_method: Optional[str] = None
    payment_method_title: Optional[str] = None
    transaction_id: Optional[str] = None
    customer_note: Optional[str] = None
    created_via: Optional[str] = None
    billing: Dict[str, Any]
    shipping: Dict[str, Any]
    last_synced_at: datetime
    sync_source: str
    line_items: Optional[List[OrderItemResponse]] = []


class OrderListResponse(BaseModel):
    """Paginated list of orders"""
    orders: List[OrderResponse]
    total: int
    page: int
    limit: int


class SaveOrdersRequest(BaseModel):
    """Request to save orders from WooCommerce"""
    orders: List[Dict[str, Any]]


class SaveOrdersResponse(BaseModel):
    """Response from saving orders"""
    created: int
    updated: int
    errors: int
    total: int

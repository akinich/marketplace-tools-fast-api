"""
================================================================================
Orders Module Schemas - Pydantic Models (Simplified)
================================================================================
Version: 3.0.0
Created: 2025-12-08
Updated: 2025-12-08

Description:
    Pydantic schemas for B2C Orders module
    - Order management (CRUD operations)
    - Manual sync with date range support

Note: Simplified version - removed stats, export, webhook schemas

================================================================================
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal


# ============================================================================
# Order Item Schemas
# ============================================================================

class OrderItemResponse(BaseModel):
    """Response schema for order items"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_id: int
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    name: str
    sku: Optional[str] = None
    quantity: int
    price: Decimal
    subtotal: Decimal
    total: Decimal
    tax: Decimal
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Order Schemas
# ============================================================================

class OrderResponse(BaseModel):
    """Response schema with all order details"""
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
    
    billing: Dict[str, Any] = Field(default_factory=dict)
    shipping: Dict[str, Any] = Field(default_factory=dict)
    
    last_synced_at: datetime
    sync_source: str
    created_at: datetime
    updated_at: datetime
    line_items: Optional[List[OrderItemResponse]] = Field(default_factory=list)


class OrderListResponse(BaseModel):
    """Paginated list of orders"""
    orders: List[OrderResponse]
    total: int
    page: int
    limit: int


# ============================================================================
# Sync Schemas
# ============================================================================

class SyncOrdersRequest(BaseModel):
    """Request to sync orders from WooCommerce API"""
    start_date: Optional[date] = Field(None, description="Start date (optional, defaults to 3 days ago)")
    end_date: Optional[date] = Field(None, description="End date (optional, defaults to today)")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate that end_date is after start_date"""
        if v and 'start_date' in info.data and info.data['start_date']:
            if v < info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class SyncOrdersResponse(BaseModel):
    """Response from order sync operation"""
    synced: int
    created: int
    updated: int
    skipped: int
    errors: int
    sync_duration_seconds: float
    sync_source: str = "api"
    start_date: date
    end_date: date


"""
================================================================================
Orders Module Schemas - Pydantic Models
================================================================================
Version: 1.0.0
Created: 2025-12-07

Description:
    Pydantic schemas for B2C Orders module including:
    - Order management (CRUD operations)
    - WooCommerce webhook handling
    - Order sync from WooCommerce API

Schemas:
    - OrderBase: Base order schema with common fields
    - OrderCreate: Schema for creating new orders
    - OrderUpdate: Schema for updating existing orders
    - OrderResponse: Response schema with all order details
    - OrderListResponse: Paginated list of orders
    - OrderItemBase: Base order item schema
    - OrderItemResponse: Order item with details
    - WooCommerceWebhookPayload: WooCommerce webhook payload
================================================================================
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Order Item Schemas
# ============================================================================

class OrderItemBase(BaseModel):
    """Base schema for order items"""
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    name: str
    sku: Optional[str] = None
    quantity: int = Field(ge=1, description="Quantity must be at least 1")
    price: Decimal = Field(default=0.00, description="Unit price")
    subtotal: Decimal = Field(default=0.00, description="Subtotal before tax")
    total: Decimal = Field(default=0.00, description="Total after tax")
    tax: Decimal = Field(default=0.00, description="Tax amount")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OrderItemCreate(OrderItemBase):
    """Schema for creating order items"""
    pass


class OrderItemResponse(OrderItemBase):
    """Response schema for order items"""
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Order Schemas
# ============================================================================

class OrderBase(BaseModel):
    """Base schema for orders"""
    woo_order_id: int = Field(..., description="WooCommerce order ID")
    order_number: str = Field(..., description="Order number")
    customer_id: Optional[int] = Field(None, description="Customer ID from woo_customers table")

    status: str = Field(default="pending", description="Order status")

    date_created: datetime = Field(..., description="Order creation date")
    date_modified: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    date_paid: Optional[datetime] = None

    currency: str = Field(default="INR", description="Currency code")
    subtotal: Decimal = Field(default=0.00, ge=0)
    total_tax: Decimal = Field(default=0.00, ge=0)
    shipping_total: Decimal = Field(default=0.00, ge=0)
    discount_total: Decimal = Field(default=0.00, ge=0)
    total: Decimal = Field(..., ge=0, description="Order total")

    payment_method: Optional[str] = None
    payment_method_title: Optional[str] = None
    transaction_id: Optional[str] = None

    customer_note: Optional[str] = None
    created_via: Optional[str] = None

    billing: Dict[str, Any] = Field(default_factory=dict, description="Billing address and contact")
    shipping: Dict[str, Any] = Field(default_factory=dict, description="Shipping address")

    @validator('status')
    def validate_status(cls, v):
        """Validate order status"""
        valid_statuses = ['pending', 'processing', 'on-hold', 'completed', 'cancelled', 'refunded', 'failed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class OrderCreate(OrderBase):
    """Schema for creating new orders"""
    line_items: List[OrderItemCreate] = Field(default_factory=list, description="Order line items")


class OrderUpdate(BaseModel):
    """Schema for updating existing orders (all fields optional)"""
    status: Optional[str] = None
    date_modified: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    date_paid: Optional[datetime] = None

    subtotal: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    shipping_total: Optional[Decimal] = None
    discount_total: Optional[Decimal] = None
    total: Optional[Decimal] = None

    payment_method: Optional[str] = None
    payment_method_title: Optional[str] = None
    transaction_id: Optional[str] = None

    customer_note: Optional[str] = None

    billing: Optional[Dict[str, Any]] = None
    shipping: Optional[Dict[str, Any]] = None

    @validator('status')
    def validate_status(cls, v):
        """Validate order status"""
        if v is not None:
            valid_statuses = ['pending', 'processing', 'on-hold', 'completed', 'cancelled', 'refunded', 'failed']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class OrderResponse(OrderBase):
    """Response schema with all order details"""
    id: int
    last_synced_at: datetime
    sync_source: str
    created_at: datetime
    updated_at: datetime
    line_items: Optional[List[OrderItemResponse]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Paginated list of orders"""
    orders: List[OrderResponse]
    total: int
    page: int
    limit: int


class OrderStatsResponse(BaseModel):
    """Order statistics response"""
    total_orders: int
    pending_orders: int
    processing_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    average_order_value: Decimal


# ============================================================================
# WooCommerce Webhook Schemas
# ============================================================================

class WooCommerceLineItem(BaseModel):
    """WooCommerce line item from webhook/API"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    name: str
    sku: Optional[str] = None
    quantity: int = 1
    price: Optional[str] = "0.00"
    subtotal: Optional[str] = "0.00"
    total: Optional[str] = "0.00"
    tax: Optional[str] = "0.00"
    meta_data: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    class Config:
        # Allow extra fields from API (e.g., taxes, image, parent_name, etc.)
        extra = "allow"


class WooCommerceWebhookPayload(BaseModel):
    """WooCommerce webhook payload structure"""
    id: int
    number: Optional[str] = None
    order_key: Optional[str] = None
    status: str
    currency: str = "INR"

    date_created: str
    date_modified: Optional[str] = None
    date_completed: Optional[str] = None
    date_paid: Optional[str] = None

    discount_total: str = "0.00"
    shipping_total: str = "0.00"
    total: str
    total_tax: str = "0.00"

    customer_id: Optional[int] = 0
    customer_note: Optional[str] = ""

    billing: Dict[str, Any] = Field(default_factory=dict)
    shipping: Dict[str, Any] = Field(default_factory=dict)

    payment_method: Optional[str] = ""
    payment_method_title: Optional[str] = ""
    transaction_id: Optional[str] = ""

    created_via: Optional[str] = ""

    line_items: List[WooCommerceLineItem] = Field(default_factory=list)

    class Config:
        # Allow extra fields from API that aren't in schema (e.g., _links, meta_data at root level)
        extra = "allow"

    @validator('number', pre=True, always=True)
    def set_order_number(cls, v, values):
        """Use id as order number if not provided"""
        if v is None and 'id' in values:
            return str(values['id'])
        return v or ""


class WebhookValidationResponse(BaseModel):
    """Response for webhook validation"""
    valid: bool
    message: str
    order_id: Optional[int] = None


class SyncOrdersRequest(BaseModel):
    """Request to sync orders from WooCommerce"""
    days: int = Field(default=3, ge=1, le=90, description="Number of days to sync (1-90)")
    force_full_sync: bool = Field(default=False, description="Force sync of all orders regardless of modification date")


class SyncOrdersResponse(BaseModel):
    """Response from order sync operation"""
    synced: int
    created: int
    updated: int
    skipped: int
    errors: int
    sync_duration_seconds: float
    sync_source: str = "api"


# ============================================================================
# Order Export Schema
# ============================================================================

class OrderExportRequest(BaseModel):
    """Request to export orders to Excel"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    order_ids: Optional[List[int]] = None

    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate date range"""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v

"""
================================================================================
WooCommerce Customer - Pydantic Schemas
================================================================================
Version: 1.0.0
Created: 2025-12-03

Schemas for WooCommerce Customer Master module
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# WOOCOMMERCE CUSTOMER SCHEMAS
# ============================================================================

class WooCustomerBase(BaseModel):
    """Base WooCommerce customer schema"""
    customer_id: int
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "customer"
    
    # Billing Address
    billing_first_name: Optional[str] = None
    billing_last_name: Optional[str] = None
    billing_company: Optional[str] = None
    billing_address_1: Optional[str] = None
    billing_address_2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postcode: Optional[str] = None
    billing_country: Optional[str] = None
    billing_email: Optional[str] = None
    billing_phone: Optional[str] = None
    
    # Shipping Address
    shipping_first_name: Optional[str] = None
    shipping_last_name: Optional[str] = None
    shipping_company: Optional[str] = None
    shipping_address_1: Optional[str] = None
    shipping_address_2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postcode: Optional[str] = None
    shipping_country: Optional[str] = None
    
    # Metadata
    is_paying_customer: bool = False
    avatar_url: Optional[str] = None
    notes: Optional[str] = None


class WooCustomerCreate(WooCustomerBase):
    """Schema for creating a WooCommerce customer"""
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class WooCustomerUpdate(BaseModel):
    """Schema for updating a WooCommerce customer (all fields optional)"""
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    
    # Billing Address
    billing_first_name: Optional[str] = None
    billing_last_name: Optional[str] = None
    billing_company: Optional[str] = None
    billing_address_1: Optional[str] = None
    billing_address_2: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postcode: Optional[str] = None
    billing_country: Optional[str] = None
    billing_email: Optional[str] = None
    billing_phone: Optional[str] = None
    
    # Shipping Address
    shipping_first_name: Optional[str] = None
    shipping_last_name: Optional[str] = None
    shipping_company: Optional[str] = None
    shipping_address_1: Optional[str] = None
    shipping_address_2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postcode: Optional[str] = None
    shipping_country: Optional[str] = None
    
    # Metadata
    is_paying_customer: Optional[bool] = None
    avatar_url: Optional[str] = None
    notes: Optional[str] = None  # User editable


class WooCustomerResponse(WooCustomerBase):
    """Schema for WooCommerce customer response"""
    id: int
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WooCustomerListResponse(BaseModel):
    """Schema for WooCommerce customer list response"""
    customers: List[WooCustomerResponse]
    total: int


# ============================================================================
# SYNC SCHEMAS
# ============================================================================

class WooCustomerSyncRequest(BaseModel):
    """Schema for WooCommerce customer sync request"""
    # No parameters needed for now, could add filters later
    pass


class WooCustomerSyncResponse(BaseModel):
    """Schema for WooCommerce customer sync response"""
    added: int
    updated: int
    skipped: int
    errors: int
    total: int = 0
    message: str


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class WooCustomerStatsResponse(BaseModel):
    """Schema for WooCommerce customer statistics"""
    total: int
    paying_customers: int
    countries: int
    india_customers: int
    new_this_month: int

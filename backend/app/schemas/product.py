"""
================================================================================
Product Management - Pydantic Schemas
================================================================================
Version: 1.0.0
Product Management Schemas

Schemas for Woo Item Master module
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductBase(BaseModel):
    """Base product schema"""
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    sku: Optional[str] = None
    product_name: str
    parent_product: Optional[str] = None
    stock_quantity: int = 0
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None
    hsn: Optional[str] = None
    zoho_name: Optional[str] = None
    usage_units: Optional[str] = None
    categories: Optional[str] = None
    attribute: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    product_status: str = "publish"


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)"""
    sku: Optional[str] = None
    product_name: Optional[str] = None
    parent_product: Optional[str] = None
    stock_quantity: Optional[int] = None
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None
    hsn: Optional[str] = None
    zoho_name: Optional[str] = None
    usage_units: Optional[str] = None
    categories: Optional[str] = None
    attribute: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    product_status: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for product list response"""
    products: List[ProductResponse]
    total: int
    page: int
    limit: int


# ============================================================================
# WOOCOMMERCE SYNC SCHEMAS
# ============================================================================

class WooCommerceSyncRequest(BaseModel):
    """Schema for WooCommerce sync request"""
    limit: int = Field(default=100, ge=1, le=1000, description="Number of products to fetch (max 1000)")
    update_existing: bool = Field(default=False, description="Update existing products with latest WooCommerce data")


class WooCommerceSyncResponse(BaseModel):
    """Schema for WooCommerce sync response"""
    added: int
    updated: int
    skipped: int
    errors: int
    message: str


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ProductStatsResponse(BaseModel):
    """Schema for product statistics"""
    total: int
    active: int
    inactive: int
    simple: int
    variations: int

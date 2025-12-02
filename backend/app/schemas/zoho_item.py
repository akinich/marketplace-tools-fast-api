"""
================================================================================
Zoho Item Management - Pydantic Schemas
================================================================================
Version: 1.0.0
Created: 2025-12-02

Schemas for Zoho Item Master module
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# ZOHO ITEM SCHEMAS
# ============================================================================

class ZohoItemBase(BaseModel):
    """Base Zoho item schema"""
    item_id: int
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    rate: Optional[float] = None
    purchase_rate: Optional[float] = None
    item_type: Optional[str] = None  # sales, purchases, sales_and_purchases, inventory
    product_type: Optional[str] = None  # goods, service
    status: str = "active"
    hsn_or_sac: Optional[str] = None
    tax_id: Optional[str] = None
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None
    is_taxable: bool = True
    unit: Optional[str] = None
    account_id: Optional[str] = None


class ZohoItemCreate(ZohoItemBase):
    """Schema for creating a Zoho item"""
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    raw_json: Optional[dict] = None


class ZohoItemUpdate(BaseModel):
    """Schema for updating a Zoho item (all fields optional)"""
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    rate: Optional[float] = None
    purchase_rate: Optional[float] = None
    item_type: Optional[str] = None
    product_type: Optional[str] = None
    status: Optional[str] = None
    hsn_or_sac: Optional[str] = None
    tax_id: Optional[str] = None
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None
    is_taxable: Optional[bool] = None
    unit: Optional[str] = None
    account_id: Optional[str] = None


class ZohoItemResponse(ZohoItemBase):
    """Schema for Zoho item response"""
    id: int
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZohoItemListResponse(BaseModel):
    """Schema for Zoho item list response"""
    items: List[ZohoItemResponse]
    total: int


# ============================================================================
# ZOHO SYNC SCHEMAS
# ============================================================================

class ZohoSyncRequest(BaseModel):
    """Schema for Zoho Books sync request"""
    force_refresh: bool = Field(
        default=False, 
        description="Force refresh all items even if recently synced"
    )


class ZohoSyncResponse(BaseModel):
    """Schema for Zoho Books sync response"""
    added: int
    updated: int
    skipped: int
    errors: int
    total: int = 0
    message: str


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ZohoItemStatsResponse(BaseModel):
    """Schema for Zoho item statistics"""
    total: int
    active: int
    inactive: int
    goods: int
    services: int
    taxable: int
    non_taxable: int

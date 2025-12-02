"""
================================================================================
Zoho Vendor Management - Pydantic Schemas
================================================================================
Version: 1.0.0
Created: 2025-12-02

Schemas for Zoho Vendor Master module
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# ZOHO VENDOR SCHEMAS
# ============================================================================

class ZohoVendorBase(BaseModel):
    """Base Zoho vendor schema"""
    contact_id: int
    contact_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    contact_person: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_terms: Optional[int] = None
    payment_terms_label: Optional[str] = None
    status: str = "active"
    gst_no: Optional[str] = None
    gst_treatment: Optional[str] = None
    pan_no: Optional[str] = None
    tax_id: Optional[str] = None
    place_of_contact: Optional[str] = None
    is_taxable: bool = True
    outstanding_balance: Optional[float] = 0
    unused_credits: Optional[float] = 0
    notes: Optional[str] = None


class ZohoVendorCreate(ZohoVendorBase):
    """Schema for creating a Zoho vendor"""
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    raw_json: Optional[dict] = None


class ZohoVendorUpdate(BaseModel):
    """Schema for updating a Zoho vendor (all fields optional)"""
    contact_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    contact_person: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_terms: Optional[int] = None
    payment_terms_label: Optional[str] = None
    status: Optional[str] = None
    gst_no: Optional[str] = None
    gst_treatment: Optional[str] = None
    pan_no: Optional[str] = None
    tax_id: Optional[str] = None
    place_of_contact: Optional[str] = None
    is_taxable: Optional[bool] = None
    outstanding_balance: Optional[float] = None
    unused_credits: Optional[float] = None
    notes: Optional[str] = None  # User editable


class ZohoVendorResponse(ZohoVendorBase):
    """Schema for Zoho vendor response"""
    id: int
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZohoVendorListResponse(BaseModel):
    """Schema for Zoho vendor list response"""
    vendors: List[ZohoVendorResponse]
    total: int


# ============================================================================
# ZOHO SYNC SCHEMAS
# ============================================================================

class ZohoVendorSyncRequest(BaseModel):
    """Schema for Zoho Books vendor sync request"""
    force_refresh: bool = Field(
        default=False,
        description="Force refresh all vendors even if recently synced"
    )


class ZohoVendorSyncResponse(BaseModel):
    """Schema for Zoho Books vendor sync response"""
    added: int
    updated: int
    skipped: int
    errors: int
    total: int = 0
    message: str


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ZohoVendorStatsResponse(BaseModel):
    """Schema for Zoho vendor statistics"""
    total: int
    active: int
    inactive: int
    with_gst: int
    without_gst: int
    with_outstanding: int

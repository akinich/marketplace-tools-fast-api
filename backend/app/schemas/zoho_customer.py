"""
================================================================================
Zoho Customer Management - Pydantic Schemas
================================================================================
Version: 1.0.0
Created: 2025-12-02

Schemas for Zoho Customer Master module
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# ZOHO CUSTOMER SCHEMAS
# ============================================================================

class ZohoCustomerBase(BaseModel):
    """Base Zoho customer schema"""
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
    customer_type: Optional[str] = None  # business, individual
    status: str = "active"
    gst_no: Optional[str] = None
    gst_treatment: Optional[str] = None
    pan_no: Optional[str] = None
    tax_id: Optional[str] = None
    place_of_contact: Optional[str] = None
    is_taxable: bool = True
    outstanding_receivable_amount: Optional[float] = 0
    unused_credits: Optional[float] = 0
    credit_limit: Optional[float] = 0
    notes: Optional[str] = None
    customer_segment: Optional[List[str]] = None  # User-editable: B2B, B2C, B2R


class ZohoCustomerCreate(ZohoCustomerBase):
    """Schema for creating a Zoho customer"""
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    raw_json: Optional[dict] = None


class ZohoCustomerUpdate(BaseModel):
    """Schema for updating a Zoho customer (all fields optional)"""
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
    customer_type: Optional[str] = None
    status: Optional[str] = None
    gst_no: Optional[str] = None
    gst_treatment: Optional[str] = None
    pan_no: Optional[str] = None
    tax_id: Optional[str] = None
    place_of_contact: Optional[str] = None
    is_taxable: Optional[bool] = None
    outstanding_receivable_amount: Optional[float] = None
    unused_credits: Optional[float] = None
    credit_limit: Optional[float] = None
    notes: Optional[str] = None  # User editable
    customer_segment: Optional[List[str]] = None  # User-editable: B2B, B2C, B2R


class ZohoCustomerResponse(ZohoCustomerBase):
    """Schema for Zoho customer response"""
    id: int
    customer_segment: Optional[List[str]] = None
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZohoCustomerListResponse(BaseModel):
    """Schema for Zoho customer list response"""
    customers: List[ZohoCustomerResponse]
    total: int


# ============================================================================
# ZOHO SYNC SCHEMAS
# ============================================================================

class ZohoCustomerSyncRequest(BaseModel):
    """Schema for Zoho Books customer sync request"""
    force_refresh: bool = Field(
        default=False,
        description="Force refresh all customers even if recently synced"
    )


class ZohoCustomerSyncResponse(BaseModel):
    """Schema for Zoho Books customer sync response"""
    added: int
    updated: int
    skipped: int
    errors: int
    total: int = 0
    message: str


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ZohoCustomerStatsResponse(BaseModel):
    """Schema for Zoho customer statistics"""
    total: int
    active: int
    inactive: int
    business: int
    individual: int
    with_gst: int
    without_gst: int
    with_outstanding: int

"""
================================================================================
Marketplace ERP - Customer Price List Schemas
================================================================================
Version: 1.0.0
Created: 2025-12-11

Pydantic models for customer price list management, including price lists,
items, history tracking, and Excel import/export.
================================================================================
"""

from pydantic import BaseModel, Field, validator, field_serializer
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# PRICE LIST SCHEMAS
# ============================================================================

class PriceListBase(BaseModel):
    """Base price list fields"""
    price_list_name: str = Field(..., min_length=1, max_length=255, description="Price list name")
    description: Optional[str] = Field(None, description="Optional description")
    valid_from: date = Field(..., description="Date from which price list is active")
    valid_to: Optional[date] = Field(None, description="Date until which price list is active (NULL = indefinite)")
    is_active: bool = Field(True, description="Manual override to enable/disable")

    @validator('valid_to')
    def validate_date_range(cls, v, values):
        """Ensure valid_to is after valid_from"""
        if v and 'valid_from' in values and v < values['valid_from']:
            raise ValueError('valid_to must be on or after valid_from')
        return v


class PriceListCreate(PriceListBase):
    """Create price list request"""
    pass


class PriceListUpdate(BaseModel):
    """Update price list request (all fields optional)"""
    price_list_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None


class PriceListResponse(PriceListBase):
    """Price list response with metadata"""
    id: int
    items_count: int = Field(0, description="Number of items in price list")
    customers_count: int = Field(0, description="Number of customers assigned")
    status: str = Field(..., description="active | expired | upcoming")
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
    @field_serializer('created_by')
    def serialize_created_by(self, value):
        """Convert UUID to string"""
        return str(value) if value else None


class PriceListListResponse(BaseModel):
    """Paginated price list list"""
    price_lists: List[PriceListResponse]
    total: int
    page: int
    limit: int


# ============================================================================
# PRICE LIST ITEM SCHEMAS
# ============================================================================

class PriceListItemBase(BaseModel):
    """Base price list item fields"""
    item_id: int = Field(..., description="Zoho item ID")
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Item price in INR")
    notes: Optional[str] = Field(None, description="Optional notes about this price")


class PriceListItemCreate(PriceListItemBase):
    """Create/update price list item"""
    pass


class PriceListItemResponse(PriceListItemBase):
    """Price list item response with item details"""
    id: int
    price_list_id: int
    item_name: str = Field(..., description="Item name from zoho_item_master")
    item_sku: Optional[str] = Field(None, description="Item SKU")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PriceListItemsResponse(BaseModel):
    """List of price list items"""
    items: List[PriceListItemResponse]
    total: int


class BulkPriceListItemCreate(BaseModel):
    """Bulk create/update price list items""" 
    items: List[PriceListItemCreate] = Field(..., description="List of items to add/update")


# ============================================================================
# PRICE HISTORY SCHEMAS
# ============================================================================

class PriceHistoryItem(BaseModel):
    """Price history entry"""
    id: int
    price_list_id: int
    item_id: Optional[int] = None
    item_name: Optional[str] = None
    field_changed: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Price history list"""
    history: List[PriceHistoryItem]
    total: int


# ============================================================================
# CUSTOMER ASSIGNMENT SCHEMAS
# ============================================================================

class CustomerPriceListInfo(BaseModel):
    """Customer with price list assignment"""
    customer_id: int
    company_name: str
    contact_name: Optional[str] = None
    price_list_id: Optional[int] = None
    price_list_name: Optional[str] = None
    price_list_status: Optional[str] = None  # active | expired | upcoming


class AssignedCustomersResponse(BaseModel):
    """Customers assigned to a price list"""
    price_list_id: int
    price_list_name: str
    customers: List[CustomerPriceListInfo]
    total: int


# ============================================================================
# PRICE RESOLUTION SCHEMAS
# ============================================================================

class ResolvedPriceResponse(BaseModel):
    """Resolved price for customer + item combination"""
    customer_id: int
    item_id: int
    price: Decimal = Field(..., max_digits=10, decimal_places=2)
    source: str = Field(..., description="price_list | zoho_default")
    price_list_id: Optional[int] = None
    price_list_name: Optional[str] = None
    date_resolved_for: date = Field(..., description="Date for which price was resolved")
    is_price_list_active: bool = Field(..., description="Whether price list is active for this date")


# ============================================================================
# EXCEL IMPORT/EXPORT SCHEMAS
# ============================================================================

class ExcelImportRow(BaseModel):
    """Single row from Excel import"""
    sku: str = Field(..., description="Item SKU")
    price: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class ExcelImportRequest(BaseModel):
    """Excel import data"""
    rows: List[ExcelImportRow]


class ExcelImportError(BaseModel):
    """Import error details"""
    row_number: int
    sku: str
    error: str


class ExcelImportResponse(BaseModel):
    """Excel import result"""
    success: bool
    items_imported: int
    items_updated: int
    items_failed: int
    errors: List[ExcelImportError] = []
    message: str


# ============================================================================
# DUPLICATE PRICE LIST SCHEMAS
# ============================================================================

class DuplicatePriceListRequest(BaseModel):
    """Duplicate price list request"""
    new_name: str = Field(..., min_length=1, max_length=255, description="Name for duplicated price list")
    copy_items: bool = Field(True, description="Whether to copy all items")
    valid_from: Optional[date] = Field(None, description="Valid from date for new list (required if copying)")
    valid_to: Optional[date] = Field(None, description="Valid to date for new list")


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class PriceListStatsResponse(BaseModel):
    """Price list statistics"""
    total_price_lists: int
    active_price_lists: int
    expired_price_lists: int
    upcoming_price_lists: int
    total_customers_with_price_lists: int
    expiring_within_30_days: int

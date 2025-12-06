"""
================================================================================
Marketplace ERP - Purchase Order Schemas
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06

Description:
  Pydantic models for purchase order request/response validation and serialization.
  Includes schemas for PO creation, updates, vendor pricing, and Zoho export.

================================================================================
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class POStatus(str, Enum):
    """Purchase order status throughout lifecycle"""
    DRAFT = "draft"
    SENT_TO_FARM = "sent_to_farm"
    GRN_GENERATED = "grn_generated"
    COMPLETED = "completed"
    EXPORTED_TO_ZOHO = "exported_to_zoho"
    CLOSED = "closed"


class PriceSource(str, Enum):
    """Source of item pricing"""
    VENDOR = "vendor"  # Tier 1: Vendor-specific price
    ZOHO = "zoho"      # Tier 2: Zoho default price
    MANUAL = "manual"  # Tier 3: Manual entry


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class POItemCreate(BaseModel):
    """Request to create/add PO item"""
    item_id: int = Field(..., gt=0, description="Zoho item ID")
    quantity: Decimal = Field(..., gt=0, decimal_places=3, description="Quantity to order")
    unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Unit price (auto-populated if None)")
    notes: Optional[str] = Field(None, max_length=500, description="Item-specific notes")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 123,
                "quantity": 100.5,
                "unit_price": 45.00,
                "notes": "Premium quality required"
            }
        }


class POCreateRequest(BaseModel):
    """Request to create new purchase order"""
    vendor_id: int = Field(..., gt=0, description="Zoho vendor ID")
    dispatch_date: date = Field(..., description="Expected dispatch/billing date (drives pricing)")
    delivery_date: date = Field(..., description="Expected delivery date")
    items: List[POItemCreate] = Field(..., min_items=1, description="PO items")
    notes: Optional[str] = Field(None, max_length=1000, description="PO-level notes")

    @validator('delivery_date')
    def delivery_after_dispatch(cls, v, values):
        """Validate delivery date is on or after dispatch date"""
        if 'dispatch_date' in values and v < values['dispatch_date']:
            raise ValueError('Delivery date must be on or after dispatch date')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "vendor_id": 5,
                "dispatch_date": "2024-12-10",
                "delivery_date": "2024-12-12",
                "items": [
                    {"item_id": 123, "quantity": 100, "unit_price": 45.00},
                    {"item_id": 124, "quantity": 50}
                ],
                "notes": "Urgent order for weekend demand"
            }
        }


class POUpdateRequest(BaseModel):
    """Request to update existing purchase order"""
    vendor_id: Optional[int] = Field(None, gt=0, description="Zoho vendor ID")
    dispatch_date: Optional[date] = Field(None, description="Expected dispatch/billing date")
    delivery_date: Optional[date] = Field(None, description="Expected delivery date")
    items: Optional[List[POItemCreate]] = Field(None, min_items=1, description="Updated PO items")
    notes: Optional[str] = Field(None, max_length=1000, description="PO-level notes")

    class Config:
        json_schema_extra = {
            "example": {
                "delivery_date": "2024-12-13",
                "notes": "Delivery date extended by 1 day"
            }
        }


class VendorPricingRequest(BaseModel):
    """Request to add/update vendor-item pricing (admin only)"""
    vendor_id: int = Field(..., gt=0, description="Zoho vendor ID")
    item_id: int = Field(..., gt=0, description="Zoho item ID")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Price per unit")
    effective_from: date = Field(..., description="Price becomes active from this date")
    effective_to: Optional[date] = Field(None, description="Price valid until this date (NULL = indefinite)")
    notes: Optional[str] = Field(None, max_length=500, description="Reason for price change")

    @validator('effective_to')
    def valid_date_range(cls, v, values):
        """Validate effective_to is on or after effective_from"""
        if v and 'effective_from' in values and v < values['effective_from']:
            raise ValueError('effective_to must be on or after effective_from')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "vendor_id": 5,
                "item_id": 123,
                "price": 45.00,
                "effective_from": "2024-12-01",
                "effective_to": "2024-12-31",
                "notes": "December seasonal pricing"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class POItemResponse(BaseModel):
    """PO item with pricing details"""
    id: int
    item_id: int
    item_name: str
    item_sku: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    price_source: str  # vendor, zoho, manual
    total_price: Decimal
    added_from_grn: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class POResponse(BaseModel):
    """Basic purchase order information"""
    id: int
    po_number: str
    vendor_id: int
    vendor_name: str
    dispatch_date: date
    delivery_date: date
    status: str
    total_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    exported_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatusChange(BaseModel):
    """Single status change in PO history"""
    from_status: Optional[str] = None
    to_status: str
    changed_by: Optional[str] = None  # User email
    changed_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PODetailResponse(POResponse):
    """Complete PO details with items and history"""
    items: List[POItemResponse] = []
    status_history: List[StatusChange] = []

    class Config:
        from_attributes = True


class POListResponse(BaseModel):
    """Paginated list of purchase orders"""
    pos: List[POResponse]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def create(cls, pos: List[POResponse], total: int, page: int, limit: int):
        """Create response with calculated pages"""
        import math
        pages = math.ceil(total / limit) if total > 0 else 1
        return cls(
            pos=pos,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )


class PriceHistoryResponse(BaseModel):
    """Vendor-item price history entry"""
    id: int
    vendor_id: int
    vendor_name: str
    item_id: int
    item_name: str
    price: Decimal
    effective_from: date
    effective_to: Optional[date] = None
    created_by: Optional[str] = None  # User email
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ActivePriceResponse(BaseModel):
    """Active price for vendor-item on specific date"""
    item_id: int
    item_name: str
    item_sku: Optional[str] = None
    price: Decimal
    source: str  # vendor or zoho
    effective_from: Optional[date] = None  # NULL if from Zoho

    class Config:
        from_attributes = True


class ExportToZohoRequest(BaseModel):
    """Request to export POs to Zoho Books"""
    po_ids: List[int] = Field(..., min_items=1, description="List of PO IDs to export")

    class Config:
        json_schema_extra = {
            "example": {
                "po_ids": [1, 2, 3]
            }
        }


# ============================================================================
# HELPER SCHEMAS
# ============================================================================

class PriceInfo(BaseModel):
    """Price information with source"""
    price: Optional[Decimal] = None
    source: str  # vendor, zoho, manual

    class Config:
        from_attributes = True

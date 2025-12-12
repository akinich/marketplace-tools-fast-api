"""
================================================================================
Marketplace ERP - Sales Order Schemas
================================================================================
Version: 1.0.0
Last Updated: 2025-12-07

Description:
  Pydantic models for sales order request/response validation and serialization.
  Includes schemas for SO creation, updates, customer pricing, and Zoho export.

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

class SOStatus(str, Enum):
    """Sales order status throughout lifecycle"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PACKING = "packing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPORTED_TO_ZOHO = "exported_to_zoho"


class PriceSource(str, Enum):
    """Source of item pricing"""
    CUSTOMER = "customer"  # Tier 1: Customer-specific price
    ITEM_RATE = "item_rate"      # Tier 2: Zoho item rate/selling price
    MANUAL = "manual"      # Tier 3: Manual entry


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SOItemCreate(BaseModel):
    """Request to create/add SO item"""
    item_id: int = Field(..., gt=0, description="Zoho item ID")
    quantity: Decimal = Field(..., gt=0, decimal_places=3, description="Quantity to order")
    unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Unit price (auto-populated if None)")
    notes: Optional[str] = Field(None, max_length=500, description="Item-specific notes")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 123,
                "quantity": 10.5,
                "unit_price": 450.00,
                "notes": "Pack separately"
            }
        }


class SOCreateRequest(BaseModel):
    """Request to create new sales order"""
    customer_id: int = Field(..., gt=0, description="Zoho customer ID")
    so_number: Optional[str] = Field(None, max_length=50, description="Custom SO number (generated if None)")

    order_date: date = Field(..., description="Date of order placement (drives pricing)")
    delivery_date: date = Field(..., description="Expected delivery date (REQUIRED)")
    order_source: Optional[str] = Field("manual", description="Source: manual, whatsapp, email, website")

    items: List[SOItemCreate] = Field(..., min_items=1, description="SO items")
    notes: Optional[str] = Field(None, max_length=1000, description="SO-level notes")

    @validator('delivery_date')
    def delivery_after_order(cls, v, values):
        """Validate delivery date is on or after order date"""
        if 'order_date' in values and v < values['order_date']:
            raise ValueError('Delivery date must be on or after order date')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": 501,
                "order_date": "2025-12-07",
                "delivery_date": "2025-12-08",
                "order_source": "whatsapp",
                "items": [
                    {"item_id": 123, "quantity": 10, "unit_price": 450.00},
                    {"item_id": 124, "quantity": 5}
                ],
                "notes": "Urgent delivery"
            }
        }


class SOUpdateRequest(BaseModel):
    """Request to update existing sales order"""
    customer_id: Optional[int] = Field(None, gt=0, description="Zoho customer ID")
    order_date: Optional[date] = Field(None, description="Date of order placement")
    delivery_date: Optional[date] = Field(None, description="Expected delivery date")
    order_source: Optional[str] = Field(None, description="Source of order")
    items: Optional[List[SOItemCreate]] = Field(None, min_items=1, description="Updated SO items")
    notes: Optional[str] = Field(None, max_length=1000, description="SO-level notes")

    class Config:
        json_schema_extra = {
            "example": {
                "delivery_date": "2025-12-09",
                "notes": "Delivery delayed by customer request"
            }
        }


class CustomerPricingRequest(BaseModel):
    """Request to add/update customer-item pricing (admin only)"""
    customer_id: int = Field(..., gt=0, description="Zoho customer ID")
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
                "customer_id": 501,
                "item_id": 123,
                "price": 440.00,
                "effective_from": "2025-12-01",
                "effective_to": "2025-12-31",
                "notes": "December discount"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SOItemResponse(BaseModel):
    """SO item with pricing details"""
    id: int
    item_id: int
    item_name: str
    item_sku: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    price_source: str  # customer, item_rate, manual
    tax_percentage: Optional[Decimal] = 0
    line_total: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SOResponse(BaseModel):
    """Basic sales order information"""
    id: int
    so_number: str
    customer_id: int
    customer_name: str
    order_date: date
    delivery_date: Optional[date] = None
    status: str
    order_source: str
    total_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    exported_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatusChange(BaseModel):
    """Single status change in SO history"""
    from_status: Optional[str] = None
    to_status: str
    changed_by: Optional[str] = None  # User email
    changed_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SODetailResponse(SOResponse):
    """Complete SO details with items and history"""
    items: List[SOItemResponse] = []
    status_history: List[StatusChange] = []

    class Config:
        from_attributes = True


class SOListResponse(BaseModel):
    """Paginated list of sales orders"""
    orders: List[SOResponse]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def create(cls, orders: List[SOResponse], total: int, page: int, limit: int):
        """Create response with calculated pages"""
        import math
        pages = math.ceil(total / limit) if total > 0 else 1
        return cls(
            orders=orders,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )


class PriceHistoryResponse(BaseModel):
    """Customer-item price history entry"""
    id: int
    customer_id: int
    customer_name: str
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
    """Active price for customer-item on specific date"""
    item_id: int
    item_name: str
    item_sku: Optional[str] = None
    price: Decimal
    source: str  # customer or item_rate
    effective_from: Optional[date] = None

    class Config:
        from_attributes = True


class ExportToZohoRequest(BaseModel):
    """Request to export SOs to Zoho Books"""
    so_ids: List[int] = Field(..., min_items=1, description="List of SO IDs to export")

    class Config:
        json_schema_extra = {
            "example": {
                "so_ids": [1, 2, 3]
            }
        }

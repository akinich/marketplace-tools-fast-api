"""
Inventory Management Module - Pydantic Schemas
Version: 1.0.0
Created: 2024-12-07

Request and response models for inventory management, stock tracking,
movements, adjustments, and reorder levels.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

VALID_LOCATIONS = ['receiving_area', 'processing_area', 'packed_warehouse', 'delivery_vehicles', 'quality_hold']
VALID_STATUSES = ['available', 'allocated', 'hold', 'in_transit', 'delivered']
VALID_MOVEMENT_TYPES = ['stock_in', 'stock_out', 'location_transfer', 'adjustment', 'allocation', 'delivery']
VALID_ADJUSTMENT_TYPES = ['increase', 'decrease', 'correction']
VALID_APPROVAL_STATUSES = ['pending_approval', 'approved', 'rejected', 'applied']


# ============================================================================
# INVENTORY SCHEMAS
# ============================================================================

class InventoryCreate(BaseModel):
    """Manual stock entry (for testing until Packing module ready)"""
    item_id: int = Field(..., gt=0, description="Zoho item ID")
    batch_id: int = Field(..., gt=0, description="Batch ID")
    location: str = Field(..., description="Storage location")
    quantity: Decimal = Field(..., gt=0, description="Stock quantity")
    grade: Optional[str] = Field(None, description="Grade (A/B/C) if applicable")
    shelf_life_days: Optional[int] = Field(None, ge=0, description="Shelf life in days")
    entry_date: Optional[datetime] = Field(None, description="Entry timestamp (defaults to now)")
    
    @validator('location')
    def validate_location(cls, v):
        if v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v
    
    @validator('grade')
    def validate_grade(cls, v):
        if v and v not in ['A', 'B', 'C']:
            raise ValueError('Grade must be A, B, or C')
        return v


class InventoryUpdate(BaseModel):
    """Update inventory record"""
    quantity: Optional[Decimal] = Field(None, gt=0)
    location: Optional[str] = None
    status: Optional[str] = None
    grade: Optional[str] = None
    shelf_life_days: Optional[int] = Field(None, ge=0)
    
    @validator('location')
    def validate_location(cls, v):
        if v and v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in VALID_STATUSES:
            raise ValueError(f'Status must be one of: {", ".join(VALID_STATUSES)}')
        return v


class InventoryResponse(BaseModel):
    """Inventory record response"""
    id: int
    item_id: int
    item_name: Optional[str] = None
    item_sku: Optional[str] = None
    batch_id: int
    batch_number: Optional[str] = None
    location: str
    quantity: Decimal
    grade: Optional[str]
    status: str
    shelf_life_days: Optional[int]
    entry_date: datetime
    expiry_date: Optional[date]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InventoryListResponse(BaseModel):
    """Paginated inventory list"""
    items: List[InventoryResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# STOCK MOVEMENTS SCHEMAS
# ============================================================================

class InventoryMovementCreate(BaseModel):
    """Record stock movement"""
    item_id: int = Field(..., gt=0)
    batch_id: int = Field(..., gt=0)
    movement_type: str
    quantity: Decimal = Field(..., gt=0)
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    
    @validator('movement_type')
    def validate_movement_type(cls, v):
        if v not in VALID_MOVEMENT_TYPES:
            raise ValueError(f'Movement type must be one of: {", ".join(VALID_MOVEMENT_TYPES)}')
        return v


class LocationTransferRequest(BaseModel):
    """Transfer stock between locations"""
    batch_id: int = Field(..., gt=0)
    from_location: str
    to_location: str
    quantity: Decimal = Field(..., gt=0)
    notes: Optional[str] = None
    
    @validator('from_location', 'to_location')
    def validate_locations(cls, v):
        if v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v
    
    @validator('to_location')
    def validate_different_locations(cls, v, values):
        if 'from_location' in values and v == values['from_location']:
            raise ValueError('To location must be different from from location')
        return v


class InventoryMovementResponse(BaseModel):
    """Stock movement record response"""
    id: int
    item_id: int
    item_name: Optional[str] = None
    batch_id: int
    batch_number: Optional[str] = None
    movement_type: str
    quantity: Decimal
    from_location: Optional[str]
    to_location: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[int]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# STOCK ADJUSTMENTS SCHEMAS
# ============================================================================

class InventoryAdjustmentRequest(BaseModel):
    """Create stock adjustment request"""
    item_id: int = Field(..., gt=0)
    batch_id: Optional[int] = Field(None, gt=0, description="Optional: can be item-level adjustment")
    location: str
    adjustment_type: str
    quantity: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=10, description="Detailed reason for adjustment")
    photo_urls: Optional[List[str]] = Field(None, description="Supporting photo evidence")
    
    @validator('location')
    def validate_location(cls, v):
        if v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v
    
    @validator('adjustment_type')
    def validate_adjustment_type(cls, v):
        if v not in VALID_ADJUSTMENT_TYPES:
            raise ValueError(f'Adjustment type must be one of: {", ".join(VALID_ADJUSTMENT_TYPES)}')
        return v


class InventoryAdjustmentApproval(BaseModel):
    """Approve or reject adjustment"""
    approved: bool
    rejection_reason: Optional[str] = None
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v, values):
        if not values.get('approved') and not v:
            raise ValueError('Rejection reason is required when rejecting')
        return v


class InventoryAdjustmentResponse(BaseModel):
    """Stock adjustment record response"""
    id: int
    item_id: int
    item_name: Optional[str] = None
    batch_id: Optional[int]
    batch_number: Optional[str] = None
    location: str
    adjustment_type: str
    quantity: Decimal
    reason: str
    photo_urls: Optional[List[str]]
    approval_status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# REORDER LEVELS SCHEMAS
# ============================================================================

class ReorderLevelConfig(BaseModel):
    """Configure reorder level for item and location"""
    item_id: int = Field(..., gt=0)
    location: str
    reorder_quantity: Decimal = Field(..., ge=0)
    alert_threshold: Decimal = Field(..., ge=0)
    is_active: bool = True
    
    @validator('location')
    def validate_location(cls, v):
        if v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v
    
    @validator('alert_threshold')
    def validate_threshold(cls, v, values):
        if 'reorder_quantity' in values and v > values['reorder_quantity']:
            raise ValueError('Alert threshold should be <= reorder quantity')
        return v


class ReorderLevelResponse(BaseModel):
    """Reorder level configuration response"""
    id: int
    item_id: int
    item_name: Optional[str] = None
    location: str
    reorder_quantity: Decimal
    alert_threshold: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LowStockAlert(BaseModel):
    """Low stock alert item"""
    item_id: int
    item_name: str
    item_sku: Optional[str]
    location: str
    current_stock: Decimal
    reorder_quantity: Decimal
    alert_threshold: Decimal
    shortage: Decimal  # alert_threshold - current_stock


# ============================================================================
# STOCK AVAILABILITY SCHEMAS
# ============================================================================

class StockAvailabilityQuery(BaseModel):
    """Query stock availability"""
    item_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    location: Optional[str] = None
    grade: Optional[str] = None
    
    @validator('location')
    def validate_location(cls, v):
        if v and v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v


class StockAvailabilityResponse(BaseModel):
    """Stock availability check result"""
    item_id: int
    item_name: str
    requested_quantity: Decimal
    available: bool
    current_stock: Decimal
    allocated_stock: Decimal
    net_available: Decimal
    shortage: Decimal
    locations: dict  # {location: quantity}


# ============================================================================
# BATCH INVENTORY SCHEMAS
# ============================================================================

class BatchInventoryView(BaseModel):
    """Batch-wise inventory breakdown"""
    batch_id: int
    batch_number: str
    item_id: int
    item_name: str
    total_quantity: Decimal
    locations: List[dict]  # [{location, quantity, status, grade}]
    movements: List[InventoryMovementResponse]


# ============================================================================
# EXPIRING ITEMS SCHEMAS
# ============================================================================

class ExpiringItem(BaseModel):
    """Item expiring soon"""
    id: int
    item_id: int
    item_name: str
    batch_id: int
    batch_number: str
    location: str
    quantity: Decimal
    grade: Optional[str]
    entry_date: datetime
    expiry_date: date
    days_until_expiry: int
    urgency: str  # critical (<2 days), warning (2-7 days), normal (>7 days)


# ============================================================================
# REPORTS SCHEMAS
# ============================================================================

class CurrentStockReportFilters(BaseModel):
    """Filters for current stock report"""
    location: Optional[str] = None
    item_id: Optional[int] = None
    status: Optional[str] = None
    include_zero_stock: bool = False


class StockMovementReportFilters(BaseModel):
    """Filters for stock movement report"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    movement_type: Optional[str] = None
    location: Optional[str] = None
    item_id: Optional[int] = None


class BatchAgeRecord(BaseModel):
    """Batch age report record"""
    batch_id: int
    batch_number: str
    item_id: int
    item_name: str
    location: str
    quantity: Decimal
    entry_date: datetime
    age_days: int
    status: str
    
    class Config:
        from_attributes = True


# ============================================================================
# STOCK ALLOCATION SCHEMAS (for Order Integration)
# ============================================================================

class StockAllocationRequest(BaseModel):
    """Allocate stock to a sales order"""
    order_id: int = Field(..., gt=0, description="Sales order ID")
    item_id: int = Field(..., gt=0, description="Item ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity to allocate")
    batch_ids: Optional[List[int]] = Field(None, description="Specific batches to allocate (optional, uses FIFO if not provided)")
    location: Optional[str] = Field('packed_warehouse', description="Location to allocate from")
    
    @validator('location')
    def validate_location(cls, v):
        if v and v not in VALID_LOCATIONS:
            raise ValueError(f'Location must be one of: {", ".join(VALID_LOCATIONS)}')
        return v


class StockDeallocationRequest(BaseModel):
    """Deallocate/release stock from cancelled order"""
    order_id: int = Field(..., gt=0, description="Sales order ID to deallocate")


class ConfirmAllocationRequest(BaseModel):
    """Confirm allocation and debit stock (order → invoice)"""
    order_id: int = Field(..., gt=0, description="Sales order ID to confirm")


class AllocationResponse(BaseModel):
    """Response for allocation operations"""
    order_id: int
    item_id: int
    item_name: str
    total_allocated: Decimal
    batches_allocated: List[Dict[str, Any]]  # [{batch_id, batch_number, quantity}]
    status: str  # allocated, deallocated, confirmed
    created_at: datetime


class AllocationStatusResponse(BaseModel):
    """Get allocation status for an order"""
    order_id: int
    allocations: List[Dict[str, Any]]
    total_allocated_quantity: Decimal
    total_confirmed_quantity: Decimal

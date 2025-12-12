"""
Pydantic schemas for Allocation Sheet system
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# ENUMS
# ============================================================================

class InvoiceStatus(str):
    PENDING = "pending"
    READY = "ready"
    INVOICED = "invoiced"


class SheetStatus(str):
    ACTIVE = "active"
    ARCHIVED = "archived"


# ============================================================================
# BATCH ALLOCATION
# ============================================================================

class BatchAllocation(BaseModel):
    """Individual batch allocation within a cell"""
    batch_id: int
    batch_number: str
    quantity: Decimal
    is_repacked: bool = False
    is_expiring_soon: bool = False


# ============================================================================
# CELL MODELS
# ============================================================================

class AllocationCellBase(BaseModel):
    """Base schema for allocation cell"""
    item_id: int
    customer_id: str
    so_id: int
    order_quantity: Decimal = Field(..., gt=0)
    sent_quantity: Optional[Decimal] = Field(None, ge=0)


class AllocationCellCreate(AllocationCellBase):
    """Schema for creating a cell"""
    sheet_id: int


class AllocationCellUpdate(BaseModel):
    """Schema for updating a cell (optimistic locking)"""
    order_quantity: Optional[Decimal] = Field(None, gt=0)
    sent_quantity: Optional[Decimal] = Field(None, ge=0)
    version: int  # For optimistic locking
    
    @validator('sent_quantity', always=True)
    def at_least_one_field(cls, v, values):
        # Check if NEITHER field was provided
        order_qty = values.get('order_quantity')
        if order_qty is None and v is None:
            raise ValueError('At least one of order_quantity or sent_quantity must be provided')
        return v


class AllocationCellResponse(AllocationCellBase):
    """Response schema with full cell data"""
    id: int
    sheet_id: int
    order_modified: bool
    invoice_status: str
    invoice_id: Optional[int]
    allocated_batches: Optional[List[BatchAllocation]]
    has_shortfall: bool  # Computed: order_quantity > sent_quantity
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SHEET MODELS
# ============================================================================

class AllocationSheetBase(BaseModel):
    """Base schema for allocation sheet"""
    delivery_date: date


class AllocationSheetCreate(AllocationSheetBase):
    """Schema for creating a sheet"""
    pass


class AllocationSheetResponse(AllocationSheetBase):
    """Response with full sheet data"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# COMPOSITE MODELS (Grid Data)
# ============================================================================

class ItemInfo(BaseModel):
    """Item information for grid display"""
    id: int
    name: str
    sku: str
    type: Optional[str] = None
    variety: Optional[str] = None
    sub_variety: Optional[str] = None


class CustomerInfo(BaseModel):
    """Customer information for grid display"""
    id: str  # Zoho customer ID
    name: str
    so_number: str
    so_id: int
    order_modified: bool = False  # Any cells modified for this customer


class AllocationGridResponse(BaseModel):
    """Complete grid data for frontend"""
    sheet_id: int
    delivery_date: date
    items: List[ItemInfo]
    customers: List[CustomerInfo]
    cells: List[AllocationCellResponse]
    totals: Dict[str, Any]  # {total_order, total_sent, shortfall}


# ============================================================================
# STATISTICS MODELS
# ============================================================================

class ItemStatistics(BaseModel):
    """Statistics per item"""
    item_id: int
    item_name: str
    total_ordered: Decimal
    total_sent: Decimal
    shortfall: Decimal
    customers_affected: int


class CustomerStatistics(BaseModel):
    """Statistics per customer"""
    customer_id: str
    customer_name: str
    total_ordered: Decimal
    total_sent: Decimal
    fulfillment_rate: float  # Percentage
    invoice_status: str


class ShortfallDetail(BaseModel):
    """Detailed shortfall record"""
    item_id: int
    item_name: str
    customer_id: str
    customer_name: str
    ordered: Decimal
    sent: Decimal
    shortage: Decimal


class StatisticsSummary(BaseModel):
    """Overall statistics for sheet"""
    total_ordered: Decimal
    total_sent: Decimal
    total_shortfall: Decimal
    fulfillment_rate: float


class AllocationStatisticsResponse(BaseModel):
    """Complete statistics response"""
    summary: StatisticsSummary
    by_item: List[ItemStatistics]
    by_customer: List[CustomerStatistics]
    shortfalls: List[ShortfallDetail]


# ============================================================================
# INVOICE GENERATION
# ============================================================================

class MarkReadyRequest(BaseModel):
    """Request to mark customer ready for invoice"""
    sheet_id: int
    customer_id: str


class GenerateInvoiceRequest(BaseModel):
    """Request to generate invoice"""
    sheet_id: int
    customer_id: str


class GenerateInvoiceResponse(BaseModel):
    """Response after invoice generation"""
    invoice_id: int
    invoice_number: str
    total_amount: Decimal
    items_invoiced: int
    stock_debited: bool


class InvoiceStatusItem(BaseModel):
    """Invoice status for one customer"""
    customer_id: str
    customer_name: str
    invoice_status: str
    items_count: int
    total_sent: Decimal
    has_shortfall: bool
    invoice_id: Optional[int]


class InvoiceStatusListResponse(BaseModel):
    """List of customers with invoice status"""
    customers: List[InvoiceStatusItem]


# ============================================================================
# AVAILABLE DATES
# ============================================================================

class AvailableDate(BaseModel):
    """Delivery date with SO count"""
    delivery_date: date
    so_count: int
    has_shortfalls: bool
    invoice_status: str  # all_pending, partial, all_invoiced


class AvailableDatesResponse(BaseModel):
    """List of available delivery dates"""
    dates: List[AvailableDate]


# ============================================================================
# UTILITY RESPONSES
# ============================================================================

class AutoFillResponse(BaseModel):
    """Response after auto-fill operation"""
    updated_cells: int
    shortfalls: List[ShortfallDetail]


class RecalculateResponse(BaseModel):
    """Response after recalculation"""
    cells_updated: int
    shortfalls_changed: int


class CellUpdateResponse(BaseModel):
    """Response after cell update"""
    cell: AllocationCellResponse
    updated_so: bool  # True if ORDER quantity changed
    recalculated_batches: bool  # True if SENT changed
    conflicts: List[str]  # Conflict messages if any

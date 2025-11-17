"""
================================================================================
Farm Management System - Inventory Module Schemas
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial inventory Pydantic models
  - Item master, batches, transactions schemas
  - Purchase orders and suppliers schemas
  - Stock operations schemas
  - FIFO response schemas
  - Alert and export schemas

================================================================================
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================


class CategoryItem(BaseModel):
    """Inventory category"""

    id: int
    category_name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CategoriesListResponse(BaseModel):
    """Categories list response"""

    categories: List[CategoryItem]


# ============================================================================
# SUPPLIER SCHEMAS
# ============================================================================


class SupplierItem(BaseModel):
    """Supplier item"""

    id: int
    supplier_name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SuppliersListResponse(BaseModel):
    """Suppliers list response"""

    suppliers: List[SupplierItem]


class CreateSupplierRequest(BaseModel):
    """Create supplier request"""

    supplier_name: str = Field(..., min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None


class UpdateSupplierRequest(BaseModel):
    """Update supplier request"""

    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================================
# ITEM MASTER SCHEMAS
# ============================================================================


class ItemMasterBase(BaseModel):
    """Base item master fields"""

    item_name: str = Field(..., min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    unit: str = Field(..., max_length=50)
    default_supplier_id: Optional[int] = None
    reorder_threshold: Decimal = Field(default=0, ge=0)
    min_stock_level: Decimal = Field(default=0, ge=0)


class CreateItemRequest(ItemMasterBase):
    """Create item master request"""

    pass


class UpdateItemRequest(BaseModel):
    """Update item master request"""

    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    default_supplier_id: Optional[int] = None
    reorder_threshold: Optional[Decimal] = Field(None, ge=0)
    min_stock_level: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ItemMasterItem(BaseModel):
    """Item master item (list view)"""

    id: int
    item_name: str
    sku: Optional[str]
    category: Optional[str]
    unit: str
    default_supplier_id: Optional[int]
    default_supplier_name: Optional[str]
    reorder_threshold: Decimal
    min_stock_level: Decimal
    current_qty: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ItemMasterDetail(ItemMasterItem):
    """Item master detail (with batches)"""

    batches: List["BatchItem"] = []


class ItemsListResponse(BaseModel):
    """Items list response"""

    items: List[ItemMasterItem]
    total: int
    page: int
    limit: int


# ============================================================================
# BATCH SCHEMAS
# ============================================================================


class BatchItem(BaseModel):
    """Inventory batch item"""

    id: int
    item_master_id: int
    item_name: Optional[str]
    batch_number: Optional[str]
    quantity_purchased: Decimal
    remaining_qty: Decimal
    unit_cost: Decimal
    purchase_date: date
    expiry_date: Optional[date]
    supplier_id: Optional[int]
    supplier_name: Optional[str]
    po_number: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BatchesListResponse(BaseModel):
    """Batches list response"""

    batches: List[BatchItem]
    total: int


class AddStockRequest(BaseModel):
    """Add stock batch request"""

    item_master_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(..., ge=0)
    purchase_date: date
    supplier_id: Optional[int] = Field(None, gt=0)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None
    po_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @validator("expiry_date")
    def expiry_must_be_future(cls, v, values):
        if v and "purchase_date" in values and v <= values["purchase_date"]:
            raise ValueError("Expiry date must be after purchase date")
        return v


class AddStockResponse(BaseModel):
    """Add stock response"""

    success: bool
    message: str
    batch_id: int
    new_total_qty: Decimal


# ============================================================================
# STOCK OPERATIONS SCHEMAS
# ============================================================================


class UseStockRequest(BaseModel):
    """Use/deduct stock request (FIFO)"""

    item_master_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    purpose: str = Field(..., min_length=1, description="Reason for using stock")
    module_reference: Optional[str] = Field(
        None, description="Module using the stock (e.g., 'biofloc')"
    )
    tank_id: Optional[int] = Field(None, description="Related tank ID if applicable")
    notes: Optional[str] = None


class BatchUsed(BaseModel):
    """Batch used in FIFO deduction"""

    batch_id: int
    batch_number: Optional[str]
    qty_from_batch: Decimal
    unit_cost: Decimal
    cost: Decimal


class UseStockResponse(BaseModel):
    """Use stock FIFO response"""

    success: bool
    message: str
    quantity_used: Decimal
    batches_used: List[BatchUsed]
    total_cost: Decimal
    weighted_avg_cost: Decimal
    new_balance: Decimal


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================


class TransactionItem(BaseModel):
    """Inventory transaction item"""

    id: int
    item_master_id: int
    item_name: Optional[str]
    batch_id: Optional[int]
    batch_number: Optional[str]
    transaction_type: str
    quantity_change: Decimal
    new_balance: Decimal
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    po_number: Optional[str]
    module_reference: Optional[str]
    tank_id: Optional[int]
    user_id: Optional[str]
    username: Optional[str]
    notes: Optional[str]
    transaction_date: datetime

    class Config:
        from_attributes = True


class TransactionsListResponse(BaseModel):
    """Transactions list response"""

    transactions: List[TransactionItem]
    total: int
    page: int
    limit: int


# ============================================================================
# PURCHASE ORDER SCHEMAS
# ============================================================================


class POItemDetail(BaseModel):
    """Purchase order item detail"""

    id: Optional[int] = None
    item_master_id: int = Field(..., gt=0)
    item_name: Optional[str] = None
    ordered_qty: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(..., ge=0)
    line_total: Optional[Decimal] = None

    class Config:
        from_attributes = True


class CreatePORequest(BaseModel):
    """Create purchase order request"""

    po_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: int = Field(..., gt=0)
    po_date: date
    expected_delivery: Optional[date] = None
    notes: Optional[str] = None
    items: List[POItemDetail] = Field(..., min_items=1)

    @validator("expected_delivery")
    def delivery_must_be_future(cls, v, values):
        if v and "po_date" in values and v < values["po_date"]:
            raise ValueError("Expected delivery date cannot be before PO date")
        return v


class UpdatePORequest(BaseModel):
    """Update purchase order request"""

    status: Optional[str] = Field(
        None,
        description="PO status: pending, approved, ordered, received, closed, cancelled",
    )
    expected_delivery: Optional[date] = None
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = [
            "pending",
            "approved",
            "ordered",
            "received",
            "closed",
            "cancelled",
        ]
        if v and v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class POListItem(BaseModel):
    """Purchase order list item"""

    id: int
    po_number: str
    supplier_id: int
    supplier_name: str
    po_date: date
    expected_delivery: Optional[date]
    status: str
    total_cost: Decimal
    items_count: int
    created_by: Optional[str]
    created_by_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PODetail(BaseModel):
    """Purchase order detail"""

    id: int
    po_number: str
    supplier_id: int
    supplier_name: str
    po_date: date
    expected_delivery: Optional[date]
    status: str
    total_cost: Decimal
    notes: Optional[str]
    created_by: Optional[str]
    created_by_name: Optional[str]
    created_at: datetime
    items: List[POItemDetail]

    class Config:
        from_attributes = True


class POsListResponse(BaseModel):
    """Purchase orders list response"""

    pos: List[POListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# ALERT SCHEMAS
# ============================================================================


class LowStockItem(BaseModel):
    """Low stock alert item"""

    id: int
    item_name: str
    category: Optional[str]
    unit: str
    current_qty: Decimal
    reorder_threshold: Decimal
    deficit: Decimal
    default_supplier_name: Optional[str]

    class Config:
        from_attributes = True


class LowStockAlertsResponse(BaseModel):
    """Low stock alerts response"""

    items: List[LowStockItem]
    total: int


class ExpiryAlertItem(BaseModel):
    """Expiring item alert"""

    batch_id: int
    item_id: int
    item_name: str
    batch_number: Optional[str]
    remaining_qty: Decimal
    unit: str
    expiry_date: date
    days_until_expiry: int
    supplier_name: Optional[str]

    class Config:
        from_attributes = True


class ExpiryAlertsResponse(BaseModel):
    """Expiry alerts response"""

    items: List[ExpiryAlertItem]
    total: int


# ============================================================================
# STOCK SUMMARY SCHEMAS
# ============================================================================


class StockLevelItem(BaseModel):
    """Stock level summary item"""

    item_id: int
    item_name: str
    category: Optional[str]
    unit: str
    total_qty: Decimal
    reorder_threshold: Decimal
    is_low_stock: bool
    batches_count: int

    class Config:
        from_attributes = True


class StockLevelsResponse(BaseModel):
    """Stock levels response"""

    items: List[StockLevelItem]
    total: int


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================


class InventoryDashboardResponse(BaseModel):
    """Inventory dashboard summary"""

    total_items: int
    active_items: int
    total_stock_value: Decimal
    low_stock_items: int
    expiring_soon_items: int
    pending_pos: int
    recent_transactions_count: int


# Forward references for nested models
ItemMasterDetail.model_rebuild()

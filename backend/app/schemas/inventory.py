"""
================================================================================
Farm Management System - Inventory Module Schemas
================================================================================
Version: 1.4.1
Last Updated: 2025-11-21

Changelog:
----------
v1.4.1 (2025-11-21):
  - BUGFIX: Added has_transactions field to ItemMasterItem schema
  - Critical fix: Backend was querying has_transactions but schema wasn't exposing it
  - This prevented delete button from showing for inactive items without transaction history
  - has_transactions is an integer count (0 = no transactions, >0 = has transactions)

v1.4.0 (2025-11-21):
  - Added POStatus enum and PO_STATUS_TRANSITIONS for workflow validation
  - Added PO receiving schemas (ReceiveItemRequest, ReceivePORequest, POReceivingItem, etc.)
  - Added PO history/audit schemas (POHistoryItem, POHistoryResponse)
  - Added line item CRUD schemas (AddPOItemRequest, UpdatePOItemRequest, etc.)
  - Added DuplicatePORequest for PO duplication
  - Added PODetailWithReceiving for enhanced PO details

v1.3.0 (2025-11-21):
  - Added default_price field to ItemMasterBase, CreateItemRequest, UpdateItemRequest, ItemMasterItem
  - Updated item master schemas to support optional default pricing (2 decimal precision)

v1.2.1 (2025-11-20):
  - CRITICAL FIX: Changed TransactionItem.tank_id from int to str (UUID as string)
  - Fixes ResponseValidationError when returning transactions with UUID tank_id
  - Aligns with database schema change (tank_id column changed to UUID)

v1.2.0 (2025-11-18):
  - Added ModuleType enum for cross-module integration
  - Added batch deduction schemas (BatchDeductionItem, BatchDeductionRequest, BatchDeductionResponse)
  - Added bulk fetch schemas (BulkFetchRequest, BulkFetchResponse)
  - Added stock reservation schemas (CreateReservationRequest, ReservationItem, etc.)
  - Enhanced cross-module integration capabilities for biofloc

v1.1.0 (2025-11-18):
  - Added CreateCategoryRequest and UpdateCategoryRequest schemas
  - Added stock adjustments schemas (CreateAdjustmentRequest, StockAdjustmentItem, AdjustmentsListResponse)
  - Enhanced category and stock management capabilities

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
from typing import Optional, List, Union
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


# ============================================================================
# MODULE TYPE ENUM
# ============================================================================


class ModuleType(str, Enum):
    """Module types for cross-module integration"""

    BIOFLOC = "biofloc"
    HATCHERY = "hatchery"
    GROWOUT = "growout"
    NURSERY = "nursery"
    GENERAL = "general"  # fallback


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================


class CategoryItem(BaseModel):
    """Inventory category"""

    id: int
    category: str  # Aliased from category_name in database
    description: Optional[str]
    created_at: datetime
    item_count: int = 0  # Count of items using this category

    class Config:
        from_attributes = True


class CategoriesListResponse(BaseModel):
    """Categories list response"""

    categories: List[CategoryItem]


class CreateCategoryRequest(BaseModel):
    """Create category request"""

    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    """Update category request"""

    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


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
    default_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
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
    default_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
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
    default_price: Optional[Decimal]
    reorder_threshold: Decimal
    min_stock_level: Decimal
    current_qty: Decimal
    is_active: bool
    created_at: datetime
    has_transactions: int = 0  # Count of transactions and PO items

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
    tank_id: Optional[str]  # Changed from int to str (UUID as string)
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
# PO STATUS WORKFLOW
# ============================================================================


class POStatus(str, Enum):
    """Valid PO statuses with workflow transitions"""

    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Status workflow: defines valid transitions from each status
PO_STATUS_TRANSITIONS = {
    "pending": ["approved", "cancelled"],
    "approved": ["ordered", "cancelled"],
    "ordered": ["partially_received", "received", "cancelled"],
    "partially_received": ["received", "closed", "cancelled"],
    "received": ["closed"],
    "closed": [],  # Terminal state
    "cancelled": [],  # Terminal state
}


# ============================================================================
# PO RECEIVING SCHEMAS
# ============================================================================


class ReceiveItemRequest(BaseModel):
    """Request to receive a single PO line item"""

    po_item_id: int = Field(..., gt=0, description="ID of the PO line item")
    received_qty: Decimal = Field(..., ge=0, description="Actual quantity received")
    actual_unit_cost: Decimal = Field(..., ge=0, description="Actual unit cost")
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None
    notes: Optional[str] = None


class ReceivePORequest(BaseModel):
    """Request to receive goods for a PO"""

    items: List[ReceiveItemRequest] = Field(..., min_items=1)
    receipt_date: date = Field(default_factory=date.today)
    close_po: bool = Field(False, description="Close PO even if partially received")
    notes: Optional[str] = None


class POReceivingItem(BaseModel):
    """Received item details"""

    id: int
    po_item_id: int
    item_master_id: int
    item_name: Optional[str]

    # Quantities
    ordered_qty: Decimal
    received_qty: Decimal

    # Prices
    po_unit_cost: Decimal
    actual_unit_cost: Decimal
    po_line_total: Decimal
    actual_line_total: Decimal

    # Details
    batch_id: Optional[int]
    batch_number: Optional[str]
    receipt_date: date
    expiry_date: Optional[date]
    notes: Optional[str]

    # Audit
    received_by: Optional[str]
    received_by_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class POReceivingSummary(BaseModel):
    """Summary of PO receiving status"""

    total_items: int
    fully_received: int
    partially_received: int
    not_received: int
    total_ordered_value: Decimal
    total_received_value: Decimal
    variance: Decimal


class ReceivePOResponse(BaseModel):
    """Response after receiving goods"""

    success: bool
    message: str
    po_id: int
    new_status: str
    items_received: List[POReceivingItem]
    batches_created: List[int]  # IDs of created inventory batches
    summary: POReceivingSummary


# ============================================================================
# PO HISTORY/AUDIT SCHEMAS
# ============================================================================


class POHistoryItem(BaseModel):
    """PO history/audit item"""

    id: int
    purchase_order_id: int
    action: str
    previous_status: Optional[str]
    new_status: Optional[str]
    change_details: Optional[dict]
    changed_by: Optional[str]
    changed_by_name: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


class POHistoryResponse(BaseModel):
    """PO history response"""

    history: List[POHistoryItem]
    total: int


# ============================================================================
# PO LINE ITEM CRUD SCHEMAS
# ============================================================================


class AddPOItemRequest(BaseModel):
    """Request to add a new item to an existing PO"""

    item_master_id: int = Field(..., gt=0)
    ordered_qty: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(..., ge=0)


class UpdatePOItemRequest(BaseModel):
    """Request to update a PO line item"""

    po_item_id: int = Field(..., gt=0)
    ordered_qty: Optional[Decimal] = Field(None, gt=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)


class AddPOItemsRequest(BaseModel):
    """Request to add multiple items to a PO"""

    items: List[AddPOItemRequest] = Field(..., min_items=1)


class UpdatePOItemsRequest(BaseModel):
    """Request to update multiple PO line items"""

    items: List[UpdatePOItemRequest] = Field(..., min_items=1)


class POItemsUpdateResponse(BaseModel):
    """Response after updating PO items"""

    success: bool
    message: str
    po_id: int
    new_total_cost: Decimal
    items_count: int


# ============================================================================
# PO DUPLICATE SCHEMA
# ============================================================================


class DuplicatePORequest(BaseModel):
    """Request to duplicate a PO"""

    new_po_number: str = Field(..., min_length=1, max_length=100)
    po_date: date = Field(default_factory=date.today)
    expected_delivery: Optional[date] = None
    supplier_id: Optional[int] = Field(None, gt=0, description="Override supplier")
    notes: Optional[str] = None

    # Option to modify items during duplication
    items: Optional[List[POItemDetail]] = Field(None, description="Override items, or None to copy all")

    @validator("expected_delivery")
    def delivery_must_be_future(cls, v, values):
        if v and "po_date" in values and v < values["po_date"]:
            raise ValueError("Expected delivery date cannot be before PO date")
        return v


# ============================================================================
# PO DETAIL WITH RECEIVING INFO
# ============================================================================


class PODetailWithReceiving(PODetail):
    """Purchase order detail with receiving information"""

    receiving: List[POReceivingItem] = []
    receiving_summary: Optional[POReceivingSummary] = None


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
# STOCK ADJUSTMENTS SCHEMAS
# ============================================================================


class CreateAdjustmentRequest(BaseModel):
    """Create stock adjustment request"""

    item_master_id: int = Field(..., gt=0)
    adjustment_type: str = Field(
        ..., description="Type: increase, decrease, recount"
    )
    quantity_change: Decimal = Field(..., description="Change in quantity (positive or negative)")
    reason: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None

    @validator("adjustment_type")
    def validate_adjustment_type(cls, v):
        valid_types = ["increase", "decrease", "recount"]
        if v not in valid_types:
            raise ValueError(f"Adjustment type must be one of: {', '.join(valid_types)}")
        return v


class StockAdjustmentItem(BaseModel):
    """Stock adjustment item"""

    id: int
    item_master_id: int
    item_name: Optional[str]
    sku: Optional[str]
    unit: Optional[str]
    adjustment_type: str
    quantity_change: Decimal
    previous_qty: Decimal
    new_qty: Decimal
    reason: str
    notes: Optional[str]
    adjusted_by: Optional[str]
    adjusted_by_name: Optional[str]
    adjustment_date: datetime

    class Config:
        from_attributes = True


class AdjustmentsListResponse(BaseModel):
    """Stock adjustments list response"""

    adjustments: List[StockAdjustmentItem]
    total: int
    page: int
    limit: int


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


# ============================================================================
# BATCH DEDUCTION SCHEMAS (Multi-item atomic operations)
# ============================================================================


class BatchDeductionItem(BaseModel):
    """Single item in batch deduction request"""

    item_id: Optional[int] = Field(None, gt=0, description="Item ID (use this OR sku)")
    sku: Optional[str] = Field(None, max_length=100, description="Item SKU (use this OR item_id)")
    quantity: Decimal = Field(..., gt=0, description="Quantity to deduct")
    notes: Optional[str] = Field(None, description="Item-specific note")

    @validator("sku")
    def validate_item_identifier(cls, v, values):
        """Ensure either item_id or sku is provided"""
        if not v and not values.get("item_id"):
            raise ValueError("Either item_id or sku must be provided")
        if v and values.get("item_id"):
            raise ValueError("Provide either item_id or sku, not both")
        return v


class BatchDeductionRequest(BaseModel):
    """Batch deduction request for multiple items in single transaction"""

    deductions: List[BatchDeductionItem] = Field(..., min_items=1, max_items=50)
    module_reference: ModuleType = Field(..., description="Module using the stock")
    tank_id: Optional[str] = Field(None, description="Tank UUID if applicable")
    batch_id: Optional[UUID] = Field(None, description="Biofloc batch UUID for tracking")
    session_number: Optional[int] = Field(None, ge=1, description="Session number (e.g., feeding session 1, 2, 3)")
    global_notes: Optional[str] = Field(None, description="Notes for entire batch operation")

    @validator("deductions")
    def validate_deductions_limit(cls, v):
        """Enforce max 50 items per batch"""
        if len(v) > 50:
            raise ValueError("Maximum 50 items allowed per batch deduction")
        return v


class BatchDeductionResultItem(BaseModel):
    """Result for single item in batch deduction"""

    item_name: str
    sku: Optional[str]
    quantity: Decimal
    cost: Decimal
    success: bool
    error: Optional[str] = None
    available: Optional[Decimal] = Field(None, description="Available quantity if failed")
    requested: Optional[Decimal] = Field(None, description="Requested quantity if failed")


class BatchDeductionResponse(BaseModel):
    """Response for batch deduction operation"""

    success: bool
    total: int
    successful: int
    failed: int
    total_cost: Decimal
    results: List[BatchDeductionResultItem]
    transaction_ids: List[int] = Field(default_factory=list, description="Transaction IDs for successful deductions")


# ============================================================================
# BULK FETCH SCHEMAS
# ============================================================================


class BulkFetchRequest(BaseModel):
    """Bulk fetch request for multiple items"""

    item_ids: Optional[List[int]] = Field(None, description="List of item IDs to fetch")
    skus: Optional[List[str]] = Field(None, description="List of SKUs to fetch")
    include_stock: bool = Field(True, description="Include current stock levels")
    include_batches: bool = Field(False, description="Include batch details")
    include_reserved: bool = Field(False, description="Include reserved quantities")

    @validator("item_ids")
    def validate_item_ids_limit(cls, v):
        """Enforce max 100 items"""
        if v and len(v) > 100:
            raise ValueError("Maximum 100 item IDs allowed per request")
        return v

    @validator("skus")
    def validate_skus_limit(cls, v, values):
        """Ensure at least one identifier provided and max 100"""
        if v and len(v) > 100:
            raise ValueError("Maximum 100 SKUs allowed per request")
        if not v and not values.get("item_ids"):
            raise ValueError("Either item_ids or skus must be provided")
        return v


class BulkFetchItemResponse(BaseModel):
    """Single item in bulk fetch response"""

    id: int
    sku: Optional[str]
    name: str
    current_qty: Decimal
    unit: str
    category: Optional[str]
    reorder_threshold: Decimal
    last_purchase_price: Optional[Decimal] = None
    reserved_qty: Optional[Decimal] = Field(None, description="Reserved quantity (if include_reserved=true)")
    available_qty: Optional[Decimal] = Field(None, description="Available = current - reserved")
    batches: Optional[List[BatchItem]] = Field(None, description="Batch details (if include_batches=true)")

    class Config:
        from_attributes = True


class BulkFetchResponse(BaseModel):
    """Response for bulk fetch operation"""

    items: List[BulkFetchItemResponse]
    total: int
    requested: int
    found: int
    not_found: List[Union[int, str]] = Field(
        default_factory=list, description="IDs or SKUs that were not found"
    )


# ============================================================================
# ITEM-MODULE MAPPING SCHEMAS
# ============================================================================


class ItemModuleMappingItem(BaseModel):
    """Item-module mapping item"""

    id: int
    item_id: int
    module_name: str
    custom_settings: dict = Field(default_factory=dict)
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CreateItemModuleMappingRequest(BaseModel):
    """Create item-module mapping request"""

    module_name: ModuleType = Field(..., description="Module that uses this item")
    custom_settings: dict = Field(default_factory=dict, description="Module-specific settings")
    is_primary: bool = Field(False, description="Is this the primary module for this item")


class ItemModuleMappingsResponse(BaseModel):
    """Item-module mappings response"""

    mappings: List[ItemModuleMappingItem]
    total: int


class ModuleConsumptionItem(BaseModel):
    """Module consumption report item"""

    item_id: int
    item_name: str
    sku: Optional[str]
    category: Optional[str]
    unit: str
    total_quantity_used: Decimal
    total_cost: Decimal
    transaction_count: int
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


class ModuleConsumptionResponse(BaseModel):
    """Module consumption report response"""

    module_name: str
    items: List[ModuleConsumptionItem]
    total_cost: Decimal
    total_items: int
    period_days: int


# ============================================================================
# STOCK RESERVATION SCHEMAS
# ============================================================================


class CreateReservationRequest(BaseModel):
    """Create stock reservation request"""

    item_id: int = Field(..., gt=0, description="Item to reserve")
    quantity: Decimal = Field(..., gt=0, description="Quantity to reserve")
    module_reference: ModuleType = Field(..., description="Module creating reservation")
    reference_id: Optional[UUID] = Field(None, description="Tank ID, batch ID, or other reference")
    duration_hours: int = Field(24, ge=1, le=720, description="Reservation duration (1-720 hours, default 24)")
    notes: Optional[str] = None


class ReservationItem(BaseModel):
    """Reservation item"""

    id: UUID
    item_id: int
    item_name: Optional[str]
    sku: Optional[str]
    quantity: Decimal
    module_reference: str
    reference_id: Optional[UUID]
    status: str
    reserved_until: datetime
    notes: Optional[str]
    created_by: UUID
    created_by_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReservationsListResponse(BaseModel):
    """Reservations list response"""

    reservations: List[ReservationItem]
    total: int


class ConfirmReservationResponse(BaseModel):
    """Response for confirming a reservation"""

    success: bool
    message: str
    reservation_id: UUID
    transaction_id: Optional[int] = None
    cost: Optional[Decimal] = None


# Forward references for nested models
ItemMasterDetail.model_rebuild()

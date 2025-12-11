from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============================================================================
# Product List Responses
# ============================================================================

class ProductItem(BaseModel):
    id: int
    product_id: int
    variation_id: Optional[int]
    product_name: str
    parent_product: Optional[str]
    sku: Optional[str]
    stock_quantity: Optional[int] = 0
    regular_price: Optional[float] = 0.0
    sale_price: Optional[float] = 0.0
    is_updatable: bool
    is_deleted: bool
    setting_notes: Optional[str]

class ProductListResponse(BaseModel):
    updatable: List[ProductItem]
    non_updatable: List[ProductItem]
    deleted: List[ProductItem]

# ============================================================================
# Update Preview/Apply
# ============================================================================

class ProductChange(BaseModel):
    db_id: int
    product_id: int
    variation_id: Optional[int]
    stock_quantity: Optional[int] = None
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None

class UpdatePreviewRequest(BaseModel):
    changes: List[ProductChange]

class ChangeDetail(BaseModel):
    field: str
    old_value: Any
    new_value: Any

class PreviewItem(BaseModel):
    db_id: int
    product_id: int
    variation_id: Optional[int]
    product_name: str
    parent_product: Optional[str]
    sku: Optional[str]
    changes: List[ChangeDetail]

class UpdatePreviewResponse(BaseModel):
    valid_changes: List[PreviewItem]
    validation_errors: List[str]
    total_changes: int

class ApplyUpdatesRequest(BaseModel):
    changes: List[PreviewItem]

class UpdateResultResponse(BaseModel):
    success_count: int
    failure_count: int
    failed_items: List[str]
    batch_id: str

# ============================================================================
# Product Settings
# ============================================================================

class ProductSettingUpdate(BaseModel):
    product_id: int
    variation_id: Optional[int]
    is_updatable: bool
    notes: Optional[str] = None

# ============================================================================
# Change History
# ============================================================================

class ChangeHistoryItem(BaseModel):
    id: int
    product_id: int
    variation_id: Optional[int]
    field_changed: str
    old_value: str
    new_value: str
    changed_by: str
    changed_by_email: Optional[str]
    batch_id: str
    change_source: str
    sync_status: str
    sync_error: Optional[str]
    sync_attempted_at: Optional[datetime]
    created_at: datetime

class ChangeHistoryResponse(BaseModel):
    items: List[ChangeHistoryItem]
    total: int

# ============================================================================
# Statistics
# ============================================================================

class StatisticsResponse(BaseModel):
    total_products: int
    updatable: int
    non_updatable: int
    deleted: int
    recent_changes: int  # Last 24 hours

# ============================================================================
# Sync Response
# ============================================================================

class SyncResponse(BaseModel):
    updated_count: int
    deleted_count: int
    unchanged_count: int
    total_products: int

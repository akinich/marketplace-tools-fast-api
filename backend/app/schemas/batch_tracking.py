"""
================================================================================
Marketplace ERP - Batch Tracking Schemas
================================================================================
Version: 1.0.0
Last Updated: 2024-12-04

Description:
  Pydantic models for batch tracking request/response validation and serialization.
  Includes enums, request schemas, response schemas, and nested models for batch
  history and documents.

================================================================================
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
import math


# ============================================================================
# ENUMS
# ============================================================================

class BatchStatus(str, Enum):
    """Batch status throughout lifecycle"""
    ORDERED = "ordered"
    RECEIVED = "received"
    IN_GRADING = "in_grading"
    IN_PACKING = "in_packing"
    IN_INVENTORY = "in_inventory"
    ALLOCATED = "allocated"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    ARCHIVED = "archived"


class BatchStage(str, Enum):
    """Stages in batch journey"""
    PO = "po"
    GRN = "grn"
    GRADING = "grading"
    PACKING = "packing"
    INVENTORY = "inventory"
    ALLOCATION = "allocation"
    DELIVERY = "delivery"


class BatchEventType(str, Enum):
    """Types of batch events"""
    CREATED = "created"
    RECEIVED = "received"
    GRADED = "graded"
    PACKED = "packed"
    MOVED_TO_INVENTORY = "moved_to_inventory"
    ALLOCATED = "allocated"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    STATUS_CHANGED = "status_changed"
    REPACKED = "repacked"


class DocumentType(str, Enum):
    """Types of documents linked to batches"""
    PO = "po"
    GRN = "grn"
    SO = "so"
    INVOICE = "invoice"
    PACKING_LABEL = "packing_label"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class GenerateBatchRequest(BaseModel):
    """Request to generate new batch number"""
    po_id: Optional[int] = Field(None, description="Purchase Order ID")
    grn_id: Optional[int] = Field(None, description="GRN ID")
    created_by: str = Field(..., description="User UUID who created the batch")

    class Config:
        json_schema_extra = {
            "example": {
                "po_id": 123,
                "grn_id": 456,
                "created_by": "user-uuid-here"
            }
        }


class RepackBatchRequest(BaseModel):
    """Request to create repacked batch"""
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for repacking")
    damaged_quantity: float = Field(..., gt=0, description="Quantity of damaged items")
    repacked_quantity: float = Field(..., gt=0, description="Quantity after repacking")
    photos: List[str] = Field(default_factory=list, description="URLs of damage photos")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Cold storage damage",
                "damaged_quantity": 10.0,
                "repacked_quantity": 8.0,
                "photos": ["https://storage.url/photo1.jpg"],
                "notes": "Some packs had condensation damage"
            }
        }


class AddBatchHistoryRequest(BaseModel):
    """Request to add event to batch history"""
    stage: BatchStage = Field(..., description="Stage of the event")
    event_type: BatchEventType = Field(..., description="Type of event")
    event_details: Optional[Dict[str, Any]] = Field(None, description="Stage-specific data")
    new_status: Optional[BatchStatus] = Field(None, description="New batch status")
    location: Optional[str] = Field(None, max_length=100, description="Physical location")

    class Config:
        json_schema_extra = {
            "example": {
                "stage": "grading",
                "event_type": "graded",
                "event_details": {
                    "grade_a": 50,
                    "grade_b": 30,
                    "grade_c": 10,
                    "wastage": 10
                },
                "new_status": "in_grading",
                "location": "processing_area"
            }
        }


class SearchBatchesRequest(BaseModel):
    """Request to search batches with filters"""
    batch_number: Optional[str] = Field(None, description="Exact or partial batch number")
    po_number: Optional[str] = Field(None, description="PO number")
    grn_number: Optional[str] = Field(None, description="GRN number")
    so_number: Optional[str] = Field(None, description="Sales Order number")
    farm_name: Optional[str] = Field(None, description="Farm name")
    item_name: Optional[str] = Field(None, description="Item name")
    customer_name: Optional[str] = Field(None, description="Customer name")
    status: Optional[BatchStatus] = Field(None, description="Batch status")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    is_archived: Optional[bool] = Field(False, description="Include archived batches")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(50, ge=1, le=100, description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_number": "B001",
                "status": "delivered",
                "date_from": "2024-12-01",
                "date_to": "2024-12-31",
                "page": 1,
                "limit": 50
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class BatchResponse(BaseModel):
    """Basic batch information"""
    batch_id: int
    batch_number: str
    status: str
    is_repacked: bool
    parent_batch_number: Optional[str] = None
    created_at: datetime
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchDocumentLink(BaseModel):
    """Document linked to batch"""
    document_type: str
    document_id: int
    document_number: Optional[str] = None


class BatchHistoryEvent(BaseModel):
    """Single event in batch history"""
    stage: str
    event_type: str
    event_details: Optional[Dict[str, Any]] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    created_by_name: Optional[str] = None


class BatchDetailResponse(BaseModel):
    """Complete batch details with history and documents"""
    batch_id: int
    batch_number: str
    status: str
    is_repacked: bool
    parent_batch_number: Optional[str] = None
    child_batch_number: Optional[str] = None
    po_id: Optional[int] = None
    grn_id: Optional[int] = None
    created_at: datetime
    archived_at: Optional[datetime] = None
    documents: List[BatchDocumentLink] = []
    history: List[BatchHistoryEvent] = []


class BatchTimelineStage(BaseModel):
    """Single stage in batch timeline"""
    stage: str
    stage_name: str
    timestamp: Optional[datetime] = None
    status: str  # completed, in_progress, pending
    details: Optional[Dict[str, Any]] = None


class BatchTimelineResponse(BaseModel):
    """Visual timeline of batch journey"""
    batch_number: str
    timeline: List[BatchTimelineStage]


class BatchSearchResult(BaseModel):
    """Single batch in search results"""
    batch_id: int
    batch_number: str
    status: str
    is_repacked: bool
    created_at: datetime
    farm: Optional[str] = None
    current_location: Optional[str] = None


class BatchSearchResponse(BaseModel):
    """Search results with pagination"""
    batches: List[BatchSearchResult]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def create(cls, batches: List[BatchSearchResult], total: int, page: int, limit: int):
        """Create response with calculated pages"""
        pages = math.ceil(total / limit) if total > 0 else 1
        return cls(
            batches=batches,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )


class RepackBatchResponse(BaseModel):
    """Response after creating repacked batch"""
    parent_batch: str
    new_batch_number: str
    new_batch_id: int
    status: str
    created_at: datetime


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_batch_number_format(batch_number: str) -> bool:
    """
    Validate batch number format (B/2526/0001 or B/2526/0001R).

    Args:
        batch_number: Batch number to validate

    Returns:
        True if valid format
    """
    import re
    # Regular batch: B/2526/0001, B/2526/0002, etc.
    # Repacked batch: B/2526/0001R, B/2526/0002R, etc.
    pattern = r'^[A-Z]+/\d{4}/\d{4,}R?$'
    return bool(re.match(pattern, batch_number))


def parse_batch_number(batch_number: str) -> Dict[str, Any]:
    """
    Parse batch number to extract components.

    Args:
        batch_number: Batch number (e.g., B/2526/0001, B/2526/0001R)

    Returns:
        Dict with: prefix, fy, number, is_repacked, parent_number
    """
    import re
    match = re.match(r'^([A-Z]+)/(\d{4})/(\d{4,})(R?)$', batch_number)
    if not match:
        raise ValueError(f"Invalid batch number format: {batch_number}")

    prefix, fy, number, repack_suffix = match.groups()
    is_repacked = bool(repack_suffix)
    parent_number = f"{prefix}/{fy}/{number}" if is_repacked else None

    return {
        "prefix": prefix,
        "financial_year": fy,
        "number": int(number),
        "is_repacked": is_repacked,
        "parent_number": parent_number
    }

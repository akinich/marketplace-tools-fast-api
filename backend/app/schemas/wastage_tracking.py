"""
================================================================================
Marketplace ERP - Wastage Tracking Schemas
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06

Description:
  Pydantic models for wastage tracking request/response validation and
  serialization. Includes enums, request schemas, response schemas for
  wastage events, photos, repacking, categories, and analytics.

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

class WastageStage(str, Enum):
    """Stages where wastage can occur"""
    RECEIVING = "receiving"
    GRADING = "grading"
    PACKING = "packing"
    COLD_STORAGE = "cold_storage"
    CUSTOMER = "customer"


class WastageType(str, Enum):
    """Types of wastage"""
    DAMAGE = "damage"
    REJECT = "reject"
    QC = "qc"
    OVERFILL = "overfill"
    PARTIAL_DAMAGE = "partial_damage"
    FULL_LOSS = "full_loss"
    CUSTOMER_CLAIM = "customer_claim"


class CostAllocation(str, Enum):
    """Who bears the cost of wastage"""
    FARM = "farm"  # Deducted from farm invoice
    US = "us"      # Absorbed in our costs


class AlertLevel(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ThresholdScopeType(str, Enum):
    """Scope types for wastage thresholds"""
    GLOBAL = "global"
    STAGE = "stage"
    FARM = "farm"
    ITEM = "item"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class PhotoUploadData(BaseModel):
    """Photo metadata for wastage event"""
    file_name: str = Field(..., description="Original filename")
    file_size_kb: Optional[int] = Field(None, description="File size in KB")
    gps_latitude: Optional[float] = Field(None, description="GPS latitude")
    gps_longitude: Optional[float] = Field(None, description="GPS longitude")
    device_info: Optional[str] = Field(None, max_length=255, description="Device/camera info")


class LogWastageRequest(BaseModel):
    """Request to log a new wastage event"""
    batch_number: str = Field(..., min_length=1, description="Batch number (e.g., B/2526/0001)")
    stage: WastageStage = Field(..., description="Stage where wastage occurred")
    wastage_type: WastageType = Field(..., description="Type of wastage")
    
    item_name: str = Field(..., min_length=1, max_length=255, description="Item name")
    quantity: float = Field(..., gt=0, description="Quantity wasted")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit (kg, pcs, boxes, etc.)")
    
    cost_allocation: CostAllocation = Field(..., description="Who bears the cost")
    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated cost in INR (auto-calculated if not provided)")
    
    reason: Optional[str] = Field(None, description="Reason for wastage (from categories)")
    notes: Optional[str] = Field(None, description="Additional notes")
    location: Optional[str] = Field(None, max_length=100, description="Physical location")
    
    # Related documents (placeholders)
    po_id: Optional[int] = Field(None, description="Purchase Order ID")
    grn_id: Optional[int] = Field(None, description="GRN ID")
    so_id: Optional[int] = Field(None, description="Sales Order ID")
    ticket_id: Optional[int] = Field(None, description="Ticket ID (customer claims)")
    
    # Photo metadata (files uploaded separately via multipart)
    photo_metadata: List[PhotoUploadData] = Field(default_factory=list, description="Photo metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_number": "B/2526/0001",
                "stage": "receiving",
                "wastage_type": "damage",
                "item_name": "Tomatoes",
                "quantity": 10.5,
                "unit": "kg",
                "cost_allocation": "farm",
                "estimated_cost": 525.00,
                "reason": "Transport damage",
                "notes": "Damaged during heavy rain",
                "location": "receiving_area",
                "po_id": 123,
                "grn_id": 456
            }
        }


class RepackRequest(BaseModel):
    """Request to initiate repacking workflow"""
    parent_batch_number: str = Field(..., description="Parent batch number")
    wastage_event_id: Optional[int] = Field(None, description="Associated wastage event ID")
    
    damaged_quantity: float = Field(..., gt=0, description="Quantity of damaged items")
    repacked_quantity: float = Field(..., gt=0, description="Quantity after repacking")
    wastage_in_repacking: float = Field(default=0, ge=0, description="Additional wastage during repacking")
    
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for repacking")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Photo metadata for repacking photos
    photo_metadata: List[PhotoUploadData] = Field(default_factory=list, description="Photo metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "parent_batch_number": "B/2526/0001",
                "wastage_event_id": 789,
                "damaged_quantity": 20.0,
                "repacked_quantity": 18.0,
                "wastage_in_repacking": 2.0,
                "reason": "Cold storage condensation damage",
                "notes": "Repacked into smaller portions"
            }
        }


class UpdateThresholdRequest(BaseModel):
    """Request to update wastage threshold"""
    threshold_percentage: float = Field(..., gt=0, description="Threshold percentage (e.g., 5.00 = 5%)")
    alert_level: AlertLevel = Field(..., description="Alert level")
    is_active: bool = Field(default=True, description="Whether threshold is active")

    class Config:
        json_schema_extra = {
            "example": {
                "threshold_percentage": 7.00,
                "alert_level": "warning",
                "is_active": true
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class WastagePhotoResponse(BaseModel):
    """Photo information in wastage event"""
    id: int
    photo_url: str
    file_name: str
    file_size_kb: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class WastageEventResponse(BaseModel):
    """Response after logging wastage event"""
    wastage_event_id: int
    event_id: str
    batch_number: str
    stage: str
    wastage_type: str
    quantity: float
    unit: str
    cost_allocation: str
    estimated_cost: Optional[float] = None
    photos_uploaded: int
    created_at: datetime

    class Config:
        from_attributes = True


class WastageEventDetail(BaseModel):
    """Detailed wastage event information"""
    event_id: str
    stage: str
    wastage_type: str
    item_name: str
    quantity: float
    unit: str
    cost_allocation: str
    estimated_cost: Optional[float] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    photos: List[WastagePhotoResponse] = []
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class CostBreakdown(BaseModel):
    """Cost breakdown by allocation"""
    farm: float = 0.0
    us: float = 0.0


class WastageByBatchResponse(BaseModel):
    """All wastage events for a specific batch"""
    batch_number: str
    total_wastage_events: int
    total_quantity_wasted: float
    total_estimated_cost: float
    cost_breakdown: CostBreakdown
    events: List[WastageEventDetail]


class WastageFarmAnalytics(BaseModel):
    """Wastage analytics for a single farm"""
    farm_name: str
    total_wastage_kg: float
    total_cost: float
    wastage_percentage: float
    breakdown_by_type: Dict[str, float]
    breakdown_by_stage: Dict[str, float]


class WastageAnalyticsByFarmResponse(BaseModel):
    """Wastage analytics by farm"""
    date_range: Dict[str, str]
    farms: List[WastageFarmAnalytics]


class WastageStageAnalytics(BaseModel):
    """Wastage analytics for a single stage"""
    stage: str
    stage_name: str
    total_wastage_kg: float
    total_cost: float
    percentage_of_total: float
    event_count: int
    avg_wastage_per_event: float
    top_reasons: List[Dict[str, Any]]


class WastageAnalyticsByStageResponse(BaseModel):
    """Wastage analytics by stage"""
    date_range: Dict[str, str]
    stages: List[WastageStageAnalytics]


class WastageProductAnalytics(BaseModel):
    """Wastage analytics for a single product"""
    item_name: str
    total_wastage_kg: float
    total_cost: float
    wastage_percentage: float
    problematic_stages: List[Dict[str, float]]


class WastageAnalyticsByProductResponse(BaseModel):
    """Wastage analytics by product"""
    date_range: Dict[str, str]
    products: List[WastageProductAnalytics]


class WastageTrendDataPoint(BaseModel):
    """Single data point in wastage trends"""
    date: str
    total_wastage_kg: float
    total_cost: float
    event_count: int


class WastageTrendsResponse(BaseModel):
    """Wastage trends over time"""
    granularity: str  # daily, weekly, monthly
    data_points: List[WastageTrendDataPoint]


class WastageCategoryResponse(BaseModel):
    """Wastage category for dropdowns"""
    id: int
    stage: str
    wastage_type: str
    reason: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class WastageThresholdResponse(BaseModel):
    """Wastage threshold configuration"""
    id: int
    scope_type: str
    scope_value: Optional[str] = None
    stage: Optional[str] = None
    threshold_percentage: float
    alert_level: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WastageAlertResponse(BaseModel):
    """Current wastage alert"""
    alert_level: str
    message: str
    farm: Optional[str] = None
    stage: Optional[str] = None
    current_percentage: float
    threshold: float
    period: str  # e.g., "last_7_days"


class RepackBatchResponse(BaseModel):
    """Response after creating repacked batch"""
    parent_batch: str
    new_batch_number: str
    new_batch_id: int
    repacking_id: int
    repacked_quantity: float
    created_at: datetime

    class Config:
        from_attributes = True


class CategoriesListResponse(BaseModel):
    """List of wastage categories"""
    categories: List[WastageCategoryResponse]


class ThresholdsListResponse(BaseModel):
    """List of wastage thresholds"""
    thresholds: List[WastageThresholdResponse]


class AlertsListResponse(BaseModel):
    """List of current alerts"""
    alerts: List[WastageAlertResponse]

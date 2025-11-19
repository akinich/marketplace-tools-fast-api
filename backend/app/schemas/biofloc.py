"""
================================================================================
Farm Management System - Biofloc Module Schemas
================================================================================
Version: 1.1.0
Last Updated: 2025-11-19

Description:
    Pydantic schemas for the biofloc aquaculture management module.
    Covers tanks, batches, feeding, sampling, mortality, water tests,
    harvests, tank inputs, grading, and reporting.

CHANGELOG:
v1.1.0 (2025-11-19):
- Added grading schemas: GradingRequest, GradingResponse, SizeGroupCreate,
  BatchGradingResult
- Support for batch splitting with proportional cost allocation

v1.0.0 (2025-11-18):
- Initial release with core biofloc schemas

================================================================================
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class TankStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"

class TankType(str, Enum):
    CIRCULAR = "circular"
    RECTANGULAR = "rectangular"
    RACEWAY = "raceway"

class BatchStatus(str, Enum):
    ACTIVE = "active"
    HARVESTED = "harvested"
    TERMINATED = "terminated"

class HarvestType(str, Enum):
    PARTIAL = "partial"
    COMPLETE = "complete"

class InputType(str, Enum):
    CHEMICAL = "chemical"
    PROBIOTIC = "probiotic"
    CARBON_SOURCE = "carbon_source"
    MINERAL = "mineral"
    OTHER = "other"

class TransferReason(str, Enum):
    INITIAL_STOCKING = "initial stocking"
    GROWTH_TRANSFER = "growth transfer"
    HARVEST = "harvest"
    MAINTENANCE = "maintenance"
    OTHER = "other"

# ============================================================================
# TANK SCHEMAS
# ============================================================================

class TankCreate(BaseModel):
    tank_name: str = Field(..., min_length=1, max_length=100)
    tank_code: str = Field(..., min_length=1, max_length=50)
    capacity_liters: Decimal = Field(..., gt=0)
    location: Optional[str] = Field(None, max_length=200)
    tank_type: TankType = TankType.CIRCULAR
    notes: Optional[str] = None

class TankUpdate(BaseModel):
    tank_name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity_liters: Optional[Decimal] = Field(None, gt=0)
    location: Optional[str] = Field(None, max_length=200)
    tank_type: Optional[TankType] = None
    status: Optional[TankStatus] = None
    notes: Optional[str] = None

class TankResponse(BaseModel):
    id: UUID
    tank_name: str
    tank_code: str
    capacity_liters: Decimal
    location: Optional[str]
    tank_type: str
    status: TankStatus
    current_batch_id: Optional[UUID]
    current_batch_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TankListResponse(BaseModel):
    tanks: List[TankResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# BATCH SCHEMAS
# ============================================================================

class BatchCreate(BaseModel):
    batch_code: str = Field(..., min_length=1, max_length=50)
    species: str = Field(..., min_length=1, max_length=100)
    source: Optional[str] = Field(None, max_length=200)
    stocking_date: date
    initial_count: int = Field(..., gt=0)
    initial_avg_weight_g: Decimal = Field(..., gt=0)
    tank_id: UUID  # Initial tank assignment
    notes: Optional[str] = None

class BatchUpdate(BaseModel):
    status: Optional[BatchStatus] = None
    notes: Optional[str] = None

class BatchResponse(BaseModel):
    id: UUID
    batch_code: str
    species: str
    source: Optional[str]
    stocking_date: date
    initial_count: int
    initial_avg_weight_g: Decimal
    initial_total_biomass_kg: Optional[Decimal]
    current_count: int
    current_avg_weight_g: Optional[Decimal]
    current_total_biomass_kg: Optional[Decimal]
    total_mortality: int
    mortality_percentage: Optional[Decimal]
    status: BatchStatus
    end_date: Optional[date]
    cycle_duration_days: Optional[int]
    total_feed_kg: Decimal
    fcr: Optional[Decimal]
    sgr: Optional[Decimal]
    survival_rate: Optional[Decimal]
    current_tank_id: Optional[UUID] = None
    current_tank_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BatchListResponse(BaseModel):
    batches: List[BatchResponse]
    total: int
    page: int
    limit: int

class BatchTransferRequest(BaseModel):
    from_tank_id: Optional[UUID] = None
    to_tank_id: UUID
    transfer_date: date
    transfer_reason: TransferReason
    fish_count: int = Field(..., gt=0)
    avg_weight_g: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

# ============================================================================
# FEEDING SCHEMAS
# ============================================================================

class FeedItem(BaseModel):
    sku: str = Field(..., min_length=1)
    quantity_kg: Decimal = Field(..., gt=0)
    notes: Optional[str] = None

class FeedingSessionCreate(BaseModel):
    tank_id: UUID
    feeding_date: date
    session_number: int = Field(1, ge=1)
    feed_time: Optional[time] = None
    feed_items: List[FeedItem] = Field(..., min_items=1)
    notes: Optional[str] = None

class FeedingSessionResponse(BaseModel):
    id: UUID
    tank_id: UUID
    tank_name: str
    batch_id: UUID
    batch_code: str
    feeding_date: date
    session_number: int
    feed_time: Optional[time]
    feed_items: List[dict]
    total_feed_kg: Decimal
    total_cost: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True

class FeedingListResponse(BaseModel):
    feedings: List[FeedingSessionResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# SAMPLING SCHEMAS
# ============================================================================

class SamplingCreate(BaseModel):
    batch_id: UUID
    tank_id: Optional[UUID] = None
    sample_date: date
    sample_size: int = Field(..., gt=0)
    avg_weight_g: Decimal = Field(..., gt=0)
    min_weight_g: Optional[Decimal] = Field(None, gt=0)
    max_weight_g: Optional[Decimal] = Field(None, gt=0)
    std_deviation_g: Optional[Decimal] = Field(None, ge=0)
    avg_length_cm: Optional[Decimal] = Field(None, gt=0)
    min_length_cm: Optional[Decimal] = Field(None, gt=0)
    max_length_cm: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

class SamplingUpdate(BaseModel):
    sample_size: Optional[int] = Field(None, gt=0)
    avg_weight_g: Optional[Decimal] = Field(None, gt=0)
    min_weight_g: Optional[Decimal] = Field(None, gt=0)
    max_weight_g: Optional[Decimal] = Field(None, gt=0)
    avg_length_cm: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

class SamplingResponse(BaseModel):
    id: UUID
    batch_id: UUID
    batch_code: str
    tank_id: Optional[UUID]
    tank_name: Optional[str]
    sample_date: date
    sample_size: int
    avg_weight_g: Decimal
    min_weight_g: Optional[Decimal]
    max_weight_g: Optional[Decimal]
    std_deviation_g: Optional[Decimal]
    avg_length_cm: Optional[Decimal]
    min_length_cm: Optional[Decimal]
    max_length_cm: Optional[Decimal]
    condition_factor: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True

class SamplingListResponse(BaseModel):
    samplings: List[SamplingResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# MORTALITY SCHEMAS
# ============================================================================

class MortalityCreate(BaseModel):
    batch_id: UUID
    tank_id: Optional[UUID] = None
    mortality_date: date
    count: int = Field(..., gt=0)
    cause: Optional[str] = Field(None, max_length=200)
    avg_weight_g: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

class MortalityResponse(BaseModel):
    id: UUID
    batch_id: UUID
    batch_code: str
    tank_id: Optional[UUID]
    tank_name: Optional[str]
    mortality_date: date
    count: int
    cause: Optional[str]
    avg_weight_g: Optional[Decimal]
    total_biomass_loss_kg: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True

class MortalityListResponse(BaseModel):
    mortalities: List[MortalityResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# WATER TEST SCHEMAS
# ============================================================================

class WaterTestCreate(BaseModel):
    tank_id: UUID
    test_date: date
    test_time: Optional[time] = None
    temperature_c: Optional[Decimal] = None
    ph: Optional[Decimal] = Field(None, ge=0, le=14)
    dissolved_oxygen_mgl: Optional[Decimal] = Field(None, ge=0)
    salinity_ppt: Optional[Decimal] = Field(None, ge=0)
    ammonia_nh3_mgl: Optional[Decimal] = Field(None, ge=0)
    nitrite_no2_mgl: Optional[Decimal] = Field(None, ge=0)
    nitrate_no3_mgl: Optional[Decimal] = Field(None, ge=0)
    alkalinity_mgl: Optional[Decimal] = Field(None, ge=0)
    hardness_mgl: Optional[Decimal] = Field(None, ge=0)
    turbidity_ntu: Optional[Decimal] = Field(None, ge=0)
    tds_mgl: Optional[Decimal] = Field(None, ge=0)
    floc_volume_mll: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None

class WaterTestResponse(BaseModel):
    id: UUID
    tank_id: UUID
    tank_name: str
    batch_id: Optional[UUID]
    batch_code: Optional[str]
    test_date: date
    test_time: Optional[time]
    temperature_c: Optional[Decimal]
    ph: Optional[Decimal]
    dissolved_oxygen_mgl: Optional[Decimal]
    salinity_ppt: Optional[Decimal]
    ammonia_nh3_mgl: Optional[Decimal]
    nitrite_no2_mgl: Optional[Decimal]
    nitrate_no3_mgl: Optional[Decimal]
    alkalinity_mgl: Optional[Decimal]
    hardness_mgl: Optional[Decimal]
    turbidity_ntu: Optional[Decimal]
    tds_mgl: Optional[Decimal]
    floc_volume_mll: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class WaterTestListResponse(BaseModel):
    water_tests: List[WaterTestResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# TANK INPUT SCHEMAS
# ============================================================================

class TankInputCreate(BaseModel):
    tank_id: UUID
    input_date: date
    input_time: Optional[time] = None
    input_type: InputType
    item_sku: Optional[str] = Field(None, max_length=50)
    item_name: str = Field(..., min_length=1, max_length=200)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    reason: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

class TankInputResponse(BaseModel):
    id: UUID
    tank_id: UUID
    tank_name: str
    batch_id: Optional[UUID]
    batch_code: Optional[str]
    input_date: date
    input_time: Optional[time]
    input_type: InputType
    item_sku: Optional[str]
    item_name: str
    quantity: Decimal
    unit: str
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    reason: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TankInputListResponse(BaseModel):
    tank_inputs: List[TankInputResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# HARVEST SCHEMAS
# ============================================================================

class HarvestCreate(BaseModel):
    batch_id: UUID
    tank_id: Optional[UUID] = None
    harvest_date: date
    harvest_type: HarvestType
    fish_count: int = Field(..., gt=0)
    total_weight_kg: Decimal = Field(..., gt=0)
    grade_a_kg: Optional[Decimal] = Field(None, ge=0)
    grade_b_kg: Optional[Decimal] = Field(None, ge=0)
    grade_c_kg: Optional[Decimal] = Field(None, ge=0)
    reject_kg: Optional[Decimal] = Field(None, ge=0)
    buyer: Optional[str] = Field(None, max_length=200)
    price_per_kg: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None

class HarvestResponse(BaseModel):
    id: UUID
    batch_id: UUID
    batch_code: str
    tank_id: Optional[UUID]
    tank_name: Optional[str]
    harvest_date: date
    harvest_type: HarvestType
    fish_count: int
    total_weight_kg: Decimal
    avg_weight_g: Decimal
    grade_a_kg: Optional[Decimal]
    grade_b_kg: Optional[Decimal]
    grade_c_kg: Optional[Decimal]
    reject_kg: Optional[Decimal]
    buyer: Optional[str]
    price_per_kg: Optional[Decimal]
    total_revenue: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True

class HarvestListResponse(BaseModel):
    harvests: List[HarvestResponse]
    total: int
    page: int
    limit: int

# ============================================================================
# GRADING & BATCH SPLITTING SCHEMAS
# ============================================================================

class SizeGroupCreate(BaseModel):
    """Represents one size group in a grading operation"""
    size_label: str = Field(..., min_length=1, max_length=10)  # A, B, C, etc.
    fish_count: int = Field(..., gt=0)
    avg_weight_g: Decimal = Field(..., gt=0)
    destination_tank_id: UUID

class GradingRequest(BaseModel):
    """Request to grade a batch and split into size groups (Option B with historical data)"""
    source_batch_id: UUID
    source_tank_id: UUID
    grading_date: date
    size_groups: List[SizeGroupCreate] = Field(..., min_items=2, max_items=3)
    notes: Optional[str] = None

class BatchGradingResult(BaseModel):
    """Result of creating one child batch from grading"""
    batch_id: UUID
    batch_code: str
    size_label: str
    fish_count: int
    avg_weight_g: Decimal
    destination_tank_id: UUID
    destination_tank_code: str

class GradingResponse(BaseModel):
    """Response after grading operation"""
    id: UUID
    source_batch_id: UUID
    source_batch_code: str
    grading_date: date
    total_fish_graded: int
    size_groups_created: int
    child_batches: List[BatchGradingResult]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# CYCLE COSTS SCHEMAS
# ============================================================================

class CycleCostsUpdate(BaseModel):
    fingerling_cost: Optional[Decimal] = Field(None, ge=0)
    feed_cost: Optional[Decimal] = Field(None, ge=0)
    chemical_cost: Optional[Decimal] = Field(None, ge=0)
    labor_cost: Optional[Decimal] = Field(None, ge=0)
    utilities_cost: Optional[Decimal] = Field(None, ge=0)
    other_cost: Optional[Decimal] = Field(None, ge=0)
    total_revenue: Optional[Decimal] = Field(None, ge=0)

class CycleCostsResponse(BaseModel):
    id: UUID
    batch_id: UUID
    batch_code: str
    fingerling_cost: Decimal
    feed_cost: Decimal
    chemical_cost: Decimal
    labor_cost: Decimal
    utilities_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal
    total_revenue: Decimal
    gross_profit: Decimal
    cost_per_kg: Optional[Decimal]
    profit_per_kg: Optional[Decimal]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class BatchPerformanceReport(BaseModel):
    batch_id: UUID
    batch_code: str
    species: str
    cycle_duration_days: int
    initial_count: int
    final_count: int
    survival_rate: Decimal
    initial_biomass_kg: Decimal
    final_biomass_kg: Decimal
    biomass_gain_kg: Decimal
    avg_daily_gain_g: Decimal
    total_feed_kg: Decimal
    fcr: Decimal
    sgr: Decimal
    total_cost: Decimal
    total_revenue: Decimal
    gross_profit: Decimal
    cost_per_kg: Decimal
    profit_per_kg: Decimal
    roi_percentage: Decimal

class DashboardStats(BaseModel):
    active_tanks: int
    available_tanks: int
    maintenance_tanks: int
    active_batches: int
    total_fish_count: int
    total_biomass_kg: Decimal
    avg_tank_utilization: Decimal
    low_do_alerts: int  # Low dissolved oxygen alerts
    high_ammonia_alerts: int
    recent_mortalities_7d: int
    upcoming_harvests: int

class TankHistoryItem(BaseModel):
    id: UUID
    batch_id: UUID
    batch_code: str
    start_date: date
    end_date: Optional[date]
    transfer_reason: str
    fish_count_at_transfer: Optional[int]
    cycle_duration_days: Optional[int]

class TankDetailResponse(BaseModel):
    tank: TankResponse
    current_batch: Optional[BatchResponse]
    recent_feedings: List[FeedingSessionResponse]
    latest_water_test: Optional[WaterTestResponse]
    history: List[TankHistoryItem]

class GrowthDataPoint(BaseModel):
    sample_date: date
    avg_weight_g: Decimal
    sample_size: int

class BatchDetailResponse(BaseModel):
    batch: BatchResponse
    growth_data: List[GrowthDataPoint]
    recent_feedings: List[FeedingSessionResponse]
    recent_mortalities: List[MortalityResponse]
    harvests: List[HarvestResponse]
    cycle_costs: Optional[CycleCostsResponse]

# ============================================================================
# FILTER AND QUERY SCHEMAS
# ============================================================================

class DateRangeFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class BatchFilter(BaseModel):
    status: Optional[BatchStatus] = None
    species: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class FeedingFilter(BaseModel):
    tank_id: Optional[UUID] = None
    batch_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

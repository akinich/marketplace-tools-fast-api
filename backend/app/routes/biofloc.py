"""
================================================================================
Farm Management System - Biofloc Module Routes
================================================================================
Version: 1.1.0
Last Updated: 2025-11-19

Description:
    REST API endpoints for biofloc aquaculture management module.
    All endpoints require biofloc module access.

CHANGELOG:
v1.1.0 (2025-11-19):
- Added POST /batches/grading endpoint for batch grading with size splitting
- Supports Option B grading with historical data inheritance

v1.0.0 (2025-11-18):
- Initial release with core biofloc endpoints

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import date
from uuid import UUID

from app.auth.dependencies import require_module_access, CurrentUser
from app.schemas.biofloc import *
from app.services import biofloc_service
import logging

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/v1/biofloc", tags=["Biofloc"])

# ============================================================================
# TANK ENDPOINTS
# ============================================================================

@router.get("/tanks", response_model=TankListResponse)
async def get_tanks(
    status: Optional[TankStatus] = None,
    is_active: Optional[bool] = True,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get list of tanks with optional filters"""
    return await biofloc_service.get_tanks_list(
        status_filter=status,
        is_active=is_active,
        page=page,
        limit=limit
    )


@router.get("/tanks/{tank_id}", response_model=TankResponse)
async def get_tank(
    tank_id: UUID,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get single tank by ID"""
    return await biofloc_service.get_tank(tank_id)


@router.post("/tanks", response_model=TankResponse, status_code=status.HTTP_201_CREATED)
async def create_tank(
    request: TankCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Create new tank"""
    return await biofloc_service.create_tank(request, UUID(current_user.id))


@router.put("/tanks/{tank_id}", response_model=TankResponse)
async def update_tank(
    tank_id: UUID,
    request: TankUpdate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Update tank"""
    return await biofloc_service.update_tank(tank_id, request)


@router.delete("/tanks/{tank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tank(
    tank_id: UUID,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Soft delete tank"""
    await biofloc_service.delete_tank(tank_id)
    return None


@router.get("/tanks/{tank_id}/history", response_model=List[TankHistoryItem])
async def get_tank_history(
    tank_id: UUID,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get batch assignment history for tank"""
    return await biofloc_service.get_tank_history(tank_id)


# ============================================================================
# BATCH ENDPOINTS
# ============================================================================

@router.get("/batches", response_model=BatchListResponse)
async def get_batches(
    status: Optional[BatchStatus] = None,
    species: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get list of batches with optional filters"""
    return await biofloc_service.get_batches_list(
        status_filter=status,
        species=species,
        page=page,
        limit=limit
    )


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get single batch by ID"""
    return await biofloc_service.get_batch(batch_id)


@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    request: BatchCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Create new batch with initial tank assignment"""
    return await biofloc_service.create_batch(request, UUID(current_user.id))


@router.post("/batches/{batch_id}/transfer", response_model=BatchResponse)
async def transfer_batch(
    batch_id: UUID,
    request: BatchTransferRequest,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Transfer batch to different tank"""
    return await biofloc_service.transfer_batch(
        batch_id,
        request,
        UUID(current_user.id)
    )


@router.post("/batches/grading", response_model=GradingResponse, status_code=status.HTTP_201_CREATED)
async def record_grading(
    request: GradingRequest,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """
    Grade a batch and split into size groups (Option B with historical data).
    Creates child batches (e.g., Batch-001-A, Batch-001-B) and assigns to destination tanks.
    Inherits proportional feed costs based on biomass at grading.
    """
    return await biofloc_service.record_grading(request, UUID(current_user.id))


@router.get("/batches/{batch_id}/performance", response_model=BatchPerformanceReport)
async def get_batch_performance(
    batch_id: UUID,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get comprehensive performance report for batch"""
    return await biofloc_service.get_batch_performance_report(batch_id)


# ============================================================================
# FEEDING ENDPOINTS
# ============================================================================

@router.get("/feeding", response_model=FeedingListResponse)
async def get_feeding_sessions(
    tank_id: Optional[UUID] = None,
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get feeding sessions with filters"""
    return await biofloc_service.get_feeding_sessions(
        tank_id=tank_id,
        batch_id=batch_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )


@router.post("/feeding", response_model=FeedingSessionResponse, status_code=status.HTTP_201_CREATED)
async def record_feeding(
    request: FeedingSessionCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Record feeding session with inventory deduction"""
    return await biofloc_service.record_feeding_session(
        request,
        UUID(current_user.id),
        current_user.full_name
    )


# ============================================================================
# SAMPLING ENDPOINTS
# ============================================================================

@router.get("/sampling", response_model=SamplingListResponse)
async def get_samplings(
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get sampling records with filters"""
    return await biofloc_service.get_samplings(
        batch_id=batch_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )


@router.post("/sampling", response_model=SamplingResponse, status_code=status.HTTP_201_CREATED)
async def record_sampling(
    request: SamplingCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Record sampling data"""
    return await biofloc_service.record_sampling(request, UUID(current_user.id))


# ============================================================================
# MORTALITY ENDPOINTS
# ============================================================================

@router.get("/mortality", response_model=MortalityListResponse)
async def get_mortalities(
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get mortality records with filters"""
    return await biofloc_service.get_mortalities(
        batch_id=batch_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )


@router.post("/mortality", response_model=MortalityResponse, status_code=status.HTTP_201_CREATED)
async def record_mortality(
    request: MortalityCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Record mortality event"""
    return await biofloc_service.record_mortality(request, UUID(current_user.id))


# ============================================================================
# WATER TEST ENDPOINTS
# ============================================================================

@router.get("/water-tests", response_model=WaterTestListResponse)
async def get_water_tests(
    tank_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get water test records with filters"""
    return await biofloc_service.get_water_tests(
        tank_id=tank_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )


@router.post("/water-tests", response_model=WaterTestResponse, status_code=status.HTTP_201_CREATED)
async def record_water_test(
    request: WaterTestCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Record water quality test"""
    return await biofloc_service.record_water_test(request, UUID(current_user.id))


# ============================================================================
# TANK INPUT ENDPOINTS
# ============================================================================

@router.get("/tank-inputs", response_model=TankInputListResponse)
async def get_tank_inputs(
    tank_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get tank input records with filters"""
    return await biofloc_service.get_tank_inputs(
        tank_id=tank_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )


@router.post("/tank-inputs", response_model=TankInputResponse, status_code=status.HTTP_201_CREATED)
async def record_tank_input(
    request: TankInputCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Record tank input (chemicals, probiotics, etc.)"""
    return await biofloc_service.record_tank_input(
        request,
        UUID(current_user.id),
        current_user.full_name
    )


# ============================================================================
# HARVEST ENDPOINTS
# ============================================================================

@router.get("/harvests", response_model=HarvestListResponse)
async def get_harvests(
    batch_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=200),
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get harvest records with filters"""
    return await biofloc_service.get_harvests(
        batch_id=batch_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )


@router.post("/harvests", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED)
async def record_harvest(
    request: HarvestCreate,
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Record harvest and finalize batch if complete"""
    return await biofloc_service.record_harvest(request, UUID(current_user.id))


# ============================================================================
# DASHBOARD & REPORTING ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: CurrentUser = Depends(require_module_access("biofloc"))
):
    """Get biofloc dashboard statistics"""
    return await biofloc_service.get_dashboard_stats()


@router.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    return {"status": "ok", "module": "biofloc"}

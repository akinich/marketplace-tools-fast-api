"""
================================================================================
Marketplace ERP - Units of Measurement Routes
================================================================================
API endpoints for managing units of measurement
================================================================================
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.schemas.units import (
    CreateUnitRequest,
    UpdateUnitRequest,
    UnitResponse,
    UnitsListResponse,
    UnitCategoryResponse,
    DeleteUnitResponse
)
from app.services import units_service
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/units", tags=["Units of Measurement"])


# ============================================================================
# GET ENDPOINTS
# ============================================================================


@router.get(
    "",
    response_model=UnitsListResponse,
    summary="List Units",
    description="Get list of units of measurement with optional filtering"
)
async def list_units(
    category: Optional[str] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False, description="Include inactive units"),
    user: dict = Depends(get_current_user)
):
    """Get list of units"""
    units = await units_service.get_units_list(
        category=category,
        include_inactive=include_inactive
    )

    return {
        "units": units,
        "total": len(units)
    }


@router.get(
    "/categories",
    response_model=list[UnitCategoryResponse],
    summary="List Unit Categories",
    description="Get list of unit categories with counts"
)
async def list_unit_categories(
    user: dict = Depends(get_current_user)
):
    """Get unit categories"""
    categories = await units_service.get_unit_categories()
    return categories


@router.get(
    "/{unit_id}",
    response_model=UnitResponse,
    summary="Get Unit",
    description="Get a single unit by ID"
)
async def get_unit(
    unit_id: int,
    user: dict = Depends(get_current_user)
):
    """Get unit by ID"""
    unit = await units_service.get_unit(unit_id)
    return unit


# ============================================================================
# CREATE ENDPOINT
# ============================================================================


@router.post(
    "",
    response_model=UnitResponse,
    summary="Create Unit",
    description="Create a new unit of measurement"
)
async def create_unit(
    request: CreateUnitRequest,
    user: dict = Depends(get_current_user)
):
    """Create a new unit"""
    unit = await units_service.create_unit(
        unit_name=request.unit_name,
        abbreviation=request.abbreviation,
        category=request.category
    )
    return unit


# ============================================================================
# UPDATE ENDPOINT
# ============================================================================


@router.put(
    "/{unit_id}",
    response_model=UnitResponse,
    summary="Update Unit",
    description="Update a unit of measurement"
)
async def update_unit(
    unit_id: int,
    request: UpdateUnitRequest,
    user: dict = Depends(get_current_user)
):
    """Update a unit"""
    unit = await units_service.update_unit(
        unit_id=unit_id,
        unit_name=request.unit_name,
        abbreviation=request.abbreviation,
        category=request.category
    )
    return unit


# ============================================================================
# DELETE ENDPOINTS
# ============================================================================


@router.delete(
    "/{unit_id}",
    response_model=DeleteUnitResponse,
    summary="Delete Unit",
    description="Permanently delete a unit (only if not in use)"
)
async def delete_unit(
    unit_id: int,
    user: dict = Depends(get_current_user)
):
    """
    Permanently delete a unit.
    Only allowed if unit is not in use by any items.
    """
    result = await units_service.delete_unit(unit_id)
    return result


@router.post(
    "/{unit_id}/deactivate",
    response_model=UnitResponse,
    summary="Deactivate Unit",
    description="Deactivate a unit (soft delete)"
)
async def deactivate_unit(
    unit_id: int,
    user: dict = Depends(get_current_user)
):
    """Deactivate a unit (can be done even if in use)"""
    unit = await units_service.deactivate_unit(unit_id)
    return unit


@router.post(
    "/{unit_id}/reactivate",
    response_model=UnitResponse,
    summary="Reactivate Unit",
    description="Reactivate a deactivated unit"
)
async def reactivate_unit(
    unit_id: int,
    user: dict = Depends(get_current_user)
):
    """Reactivate a deactivated unit"""
    unit = await units_service.reactivate_unit(unit_id)
    return unit

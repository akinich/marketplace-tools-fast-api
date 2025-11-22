"""
================================================================================
Farm Management System - Units of Measurement Schemas
================================================================================
Pydantic models for request/response validation
================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class CreateUnitRequest(BaseModel):
    """Request schema for creating a unit"""
    unit_name: str = Field(..., min_length=1, max_length=50, description="Full name of the unit")
    abbreviation: Optional[str] = Field(None, max_length=10, description="Short form (e.g., 'kg')")
    category: Optional[str] = Field(None, max_length=50, description="Category: weight, volume, count, etc.")


class UpdateUnitRequest(BaseModel):
    """Request schema for updating a unit"""
    unit_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Full name of the unit")
    abbreviation: Optional[str] = Field(None, max_length=10, description="Short form")
    category: Optional[str] = Field(None, max_length=50, description="Category")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class UnitResponse(BaseModel):
    """Response schema for a single unit"""
    id: int
    unit_name: str
    abbreviation: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    item_count: Optional[int] = Field(None, description="Number of items using this unit")

    class Config:
        from_attributes = True


class UnitsListResponse(BaseModel):
    """Response schema for list of units"""
    units: list[UnitResponse]
    total: int


class UnitCategoryResponse(BaseModel):
    """Response schema for unit category summary"""
    category: Optional[str]
    total_units: int
    active_units: int

    class Config:
        from_attributes = True


class DeleteUnitResponse(BaseModel):
    """Response schema for delete operation"""
    success: bool
    message: str
    unit_id: int
    unit_name: str

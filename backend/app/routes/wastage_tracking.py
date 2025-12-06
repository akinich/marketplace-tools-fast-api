"""
================================================================================
Marketplace ERP - Wastage Tracking Routes
================================================================================
Version: 1.0.0
Last Updated: 2024-12-06

Description:
  API endpoints for wastage tracking module. Provides wastage event logging,
  photo documentation, repacking workflow, analytics, and threshold management.

Endpoints:
  POST   /wastage/log                      - Log wastage with photos
  GET    /wastage/by-batch/{batch_number}  - Get all wastage for batch
  GET    /wastage/analytics/by-farm        - Farm analytics
  GET    /wastage/analytics/by-stage       - Stage analytics
  GET    /wastage/analytics/by-product     - Product analytics
  GET    /wastage/analytics/trends         - Time series trends
  POST   /wastage/repack                   - Initiate repacking
  GET    /wastage/categories               - Dropdown options
  GET    /wastage/thresholds               - Get thresholds
  PUT    /wastage/thresholds/{id}          - Update threshold
  GET    /wastage/alerts                   - Current alerts

================================================================================
"""

from fastapi import APIRouter, Depends, Query, File, UploadFile, Form, HTTPException, status
from typing import Optional, List
import json

from app.schemas.wastage_tracking import (
    LogWastageRequest, RepackRequest, UpdateThresholdRequest,
    WastageEventResponse, WastageByBatchResponse,
    WastageAnalyticsByFarmResponse, WastageAnalyticsByStageResponse,
    WastageAnalyticsByProductResponse, WastageTrendsResponse,
    CategoriesListResponse, ThresholdsListResponse, AlertsListResponse,
    WastageThresholdResponse, RepackBatchResponse
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import wastage_tracking_service

router = APIRouter()


# ============================================================================
# WASTAGE LOGGING
# ============================================================================

@router.post("/wastage/log", response_model=WastageEventResponse, status_code=status.HTTP_201_CREATED)
async def log_wastage(
    data: str = Form(..., description="JSON string of LogWastageRequest"),
    photos: List[UploadFile] = File(..., description="Wastage photos (minimum 1)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Log a new wastage event with photo documentation.
    
    **Required:**
    - Minimum 1 photo
    - Batch must exist and be active
    - All mandatory fields in request
    
    **Process:**
    1. Validates batch exists
    2. Uploads photos to Supabase Storage
    3. Creates wastage event record
    4. Links photos to event
    5. Updates batch history
    
    **Cost Allocation:**
    - `farm`: Deducted from farm invoice
    - `us`: Absorbed in our costs
    
    **Default Allocation:**
    - Receiving stage: `farm`
    - All other stages: `us`
    """
    try:
        # Parse JSON data from form
        request = LogWastageRequest(**json.loads(data))
        
        # Log wastage event
        result = await wastage_tracking_service.log_wastage_event(
            request=request,
            photos=photos,
            created_by=str(current_user.id)
        )
        
        return result
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in data field"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log wastage: {str(e)}"
        )


# ============================================================================
# WASTAGE RETRIEVAL
# ============================================================================

@router.get("/wastage/by-batch/{batch_number:path}", response_model=WastageByBatchResponse)
async def get_wastage_by_batch(
    batch_number: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get all wastage events for a specific batch.
    
    Returns:
    - Total wastage events count
    - Total quantity wasted
    - Total estimated cost
    - Cost breakdown (farm vs us)
    - Detailed list of all events with photos
    
    **Path Parameters:**
    - batch_number: Batch number (e.g., B/2526/0001)
    """
    try:
        result = await wastage_tracking_service.get_wastage_by_batch(batch_number)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wastage data: {str(e)}"
        )


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/wastage/analytics/by-farm", response_model=WastageAnalyticsByFarmResponse)
async def get_analytics_by_farm(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    farm_id: Optional[int] = Query(None, description="Optional farm filter"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get wastage analytics grouped by farm.
    
    **Query Parameters:**
    - date_from: Start date (default: 30 days ago)
    - date_to: End date (default: today)
    - farm_id: Optional farm filter
    
    **Returns:**
    - Total wastage per farm
    - Cost breakdown
    - Wastage percentage
    - Breakdown by type and stage
    
    **Permissions:** Admin or Manager
    """
    try:
        result = await wastage_tracking_service.get_wastage_analytics_by_farm(
            date_from=date_from,
            date_to=date_to,
            farm_id=farm_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/wastage/analytics/by-stage", response_model=WastageAnalyticsByStageResponse)
async def get_analytics_by_stage(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get wastage analytics grouped by stage.
    
    **Returns:**
    - Total wastage per stage
    - Percentage of total wastage
    - Event count
    - Average wastage per event
    - Top reasons for each stage
    
    **Permissions:** Admin or Manager
    """
    try:
        result = await wastage_tracking_service.get_wastage_analytics_by_stage(
            date_from=date_from,
            date_to=date_to
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/wastage/analytics/by-product", response_model=WastageAnalyticsByProductResponse)
async def get_analytics_by_product(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    item_name: Optional[str] = Query(None, description="Optional item filter"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get wastage analytics grouped by product/item.
    
    **Returns:**
    - Total wastage per product
    - Cost breakdown
    - Wastage percentage
    - Problematic stages (highest wastage)
    
    **Permissions:** Admin or Manager
    """
    try:
        result = await wastage_tracking_service.get_wastage_analytics_by_product(
            date_from=date_from,
            date_to=date_to,
            item_name=item_name
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/wastage/analytics/trends", response_model=WastageTrendsResponse)
async def get_wastage_trends(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("daily", description="Granularity: daily, weekly, monthly"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get wastage trends over time (time series data).
    
    **Query Parameters:**
    - granularity: 'daily', 'weekly', or 'monthly'
    
    **Returns:**
    - Time series data points
    - Total wastage per period
    - Total cost per period
    - Event count per period
    
    **Permissions:** Admin or Manager
    """
    try:
        # Validate granularity
        if granularity not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Granularity must be 'daily', 'weekly', or 'monthly'"
            )
        
        result = await wastage_tracking_service.get_wastage_trends(
            date_from=date_from,
            date_to=date_to,
            granularity=granularity
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trends: {str(e)}"
        )


# ============================================================================
# REPACKING WORKFLOW
# ============================================================================

@router.post("/wastage/repack", response_model=RepackBatchResponse, status_code=status.HTTP_201_CREATED)
async def initiate_repacking(
    data: str = Form(..., description="JSON string of RepackRequest"),
    photos: List[UploadFile] = File(..., description="Repacking photos"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Initiate repacking workflow for damaged items.
    
    **Process:**
    1. Validates parent batch exists
    2. Checks parent not already repacked
    3. Creates new batch with R suffix (e.g., B/2526/0001R)
    4. Creates repacking record
    5. Uploads photos
    
    **Validation:**
    - Parent batch must exist
    - Parent batch cannot already have a repacked child
    - Repacked quantity must be <= damaged quantity
    
    **Returns:**
    - Parent batch number
    - New batch number (with R suffix)
    - Repacking ID
    - Repacked quantity
    
    **Permissions:** User with packing/inventory access
    """
    try:
        # Parse JSON data
        request = RepackRequest(**json.loads(data))
        
        # Initiate repacking
        result = await wastage_tracking_service.initiate_repacking(
            request=request,
            photos=photos,
            created_by=str(current_user.id)
        )
        
        return result
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in data field"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate repacking: {str(e)}"
        )


# ============================================================================
# CATEGORIES & THRESHOLDS
# ============================================================================

@router.get("/wastage/categories", response_model=CategoriesListResponse)
async def get_wastage_categories(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get wastage categories for dropdown selection.
    
    **Query Parameters:**
    - stage: Optional stage filter (receiving, grading, packing, cold_storage, customer)
    
    **Returns:**
    - List of predefined wastage reasons by stage and type
    - Used for consistent categorization
    
    **Permissions:** Any authenticated user
    """
    try:
        result = await wastage_tracking_service.get_wastage_categories(stage=stage)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.get("/wastage/thresholds", response_model=ThresholdsListResponse)
async def get_wastage_thresholds(
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get configured wastage thresholds.
    
    **Returns:**
    - List of all thresholds
    - Scope type (global, stage, farm, item)
    - Threshold percentage
    - Alert level (critical, warning, info)
    
    **Permissions:** Admin only
    """
    try:
        result = await wastage_tracking_service.get_wastage_thresholds()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get thresholds: {str(e)}"
        )


@router.put("/wastage/thresholds/{threshold_id}", response_model=WastageThresholdResponse)
async def update_wastage_threshold(
    threshold_id: int,
    request: UpdateThresholdRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Update wastage threshold configuration.
    
    **Path Parameters:**
    - threshold_id: Threshold ID to update
    
    **Request Body:**
    - threshold_percentage: New threshold percentage
    - alert_level: Alert level (critical, warning, info)
    - is_active: Whether threshold is active
    
    **Permissions:** Admin only
    """
    try:
        result = await wastage_tracking_service.update_wastage_threshold(
            threshold_id=threshold_id,
            request=request
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update threshold: {str(e)}"
        )


@router.get("/wastage/alerts", response_model=AlertsListResponse)
async def get_wastage_alerts(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get current wastage alerts based on thresholds.
    
    **Returns:**
    - List of active alerts
    - Alert level (critical, warning, info)
    - Message describing the alert
    - Current wastage percentage
    - Threshold exceeded
    - Time period
    
    **Permissions:** Admin or Manager
    """
    try:
        result = await wastage_tracking_service.get_current_alerts()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )

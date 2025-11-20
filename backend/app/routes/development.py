"""
================================================================================
Farm Management System - Development Planning Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-20

Description:
  FastAPI routes for development planning and feature tracking module.
  Provides endpoints for managing features, implementation steps, and comments.

Endpoints:
  Feature Management:
    GET    /features         - List all features with pagination and filtering
    GET    /features/stats   - Get feature statistics by status and priority
    GET    /features/{id}    - Get single feature with steps and comments
    POST   /features         - Create new feature (admin only)
    PUT    /features/{id}    - Update feature (admin only)
    DELETE /features/{id}    - Delete feature (admin only)

  Step Management:
    POST   /features/{id}/steps       - Add step to feature
    PUT    /steps/{id}                - Update step status/details
    DELETE /steps/{id}                - Delete step
    POST   /features/{id}/steps/reorder - Reorder steps for a feature

  Comment Management:
    POST   /features/{id}/comments    - Add comment to feature
    DELETE /comments/{id}             - Delete comment (own or admin)

Changelog:
----------
v1.0.0 (2025-11-20):
  - Initial implementation of development planning routes
  - Feature CRUD with status (planned, in_development, testing, completed, on_hold)
  - Priority levels (low, medium, high, critical)
  - Step management with ordering and status tracking
  - Comment system with user attribution
  - Admin-only write operations, all users can read and comment
  - Pagination and filtering support for feature lists

================================================================================
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Optional, List

from app.schemas.development import (
    FeatureStatus, FeaturePriority,
    CreateFeatureRequest, UpdateFeatureRequest,
    CreateStepRequest, UpdateStepRequest, ReorderStepsRequest,
    CreateCommentRequest,
    FeatureResponse, FeatureDetailResponse, FeaturesListResponse,
    StepResponse, CommentResponse, FeatureStatsResponse
)
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user, require_admin
from app.services import development_service

router = APIRouter()


# ============================================================================
# FEATURE ENDPOINTS
# ============================================================================


@router.get("", response_model=FeaturesListResponse)
async def list_features(
    status: Optional[FeatureStatus] = Query(None, description="Filter by status"),
    priority: Optional[FeaturePriority] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all features. Everyone can view."""
    return await development_service.get_features_list(
        feature_status=status,
        priority=priority,
        page=page,
        limit=limit,
    )


@router.get("/stats", response_model=FeatureStatsResponse)
async def get_feature_stats(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get feature statistics."""
    return await development_service.get_feature_stats()


@router.get("/{feature_id}", response_model=FeatureDetailResponse)
async def get_feature(
    feature_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a single feature with steps and comments."""
    return await development_service.get_feature_by_id(feature_id)


@router.post("", response_model=FeatureDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    request: CreateFeatureRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Create a new feature. Admin only."""
    return await development_service.create_feature(request, admin.id)


@router.put("/{feature_id}", response_model=FeatureDetailResponse)
async def update_feature(
    feature_id: int,
    request: UpdateFeatureRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Update a feature. Admin only."""
    return await development_service.update_feature(feature_id, request)


@router.delete("/{feature_id}")
async def delete_feature(
    feature_id: int,
    admin: CurrentUser = Depends(require_admin),
):
    """Delete a feature. Admin only."""
    return await development_service.delete_feature(feature_id)


# ============================================================================
# STEP ENDPOINTS
# ============================================================================


@router.post("/{feature_id}/steps", response_model=StepResponse, status_code=status.HTTP_201_CREATED)
async def create_step(
    feature_id: int,
    request: CreateStepRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Add a step to a feature. Admin only."""
    return await development_service.create_step(feature_id, request)


@router.put("/steps/{step_id}", response_model=StepResponse)
async def update_step(
    step_id: int,
    request: UpdateStepRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Update a step. Admin only."""
    return await development_service.update_step(step_id, request)


@router.delete("/steps/{step_id}")
async def delete_step(
    step_id: int,
    admin: CurrentUser = Depends(require_admin),
):
    """Delete a step. Admin only."""
    return await development_service.delete_step(step_id)


@router.post("/{feature_id}/steps/reorder", response_model=List[StepResponse])
async def reorder_steps(
    feature_id: int,
    request: ReorderStepsRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Reorder steps for a feature. Admin only."""
    return await development_service.reorder_steps(feature_id, request.step_ids)


# ============================================================================
# COMMENT ENDPOINTS
# ============================================================================


@router.post("/{feature_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    feature_id: int,
    request: CreateCommentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a comment to a feature. Everyone can comment."""
    return await development_service.add_comment(feature_id, request, current_user.id)


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a comment. Users can delete own, admins can delete any."""
    is_admin = current_user.role.lower() == "admin"
    return await development_service.delete_comment(comment_id, current_user.id, is_admin)

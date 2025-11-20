"""
================================================================================
Farm Management System - Development Planning Service Layer
================================================================================
Version: 1.0.1
Last Updated: 2025-11-20

Description:
  Service layer for development planning - track features, steps, and progress.

Changelog:
----------
v1.0.1 (2025-11-20):
  - Fixed SQL queries to join with auth.users table for email column
  - Changed from 'up.email' to 'au.email' in all queries
  - Resolved "column up.email does not exist" error
  - Affected functions: get_features_list(), get_feature_by_id(), add_comment()

v1.0.0 (2025-11-20):
  - Initial implementation of development planning service
  - Feature CRUD operations with status and priority tracking
  - Step management with ordering and status tracking
  - Comment system for features
  - Statistics and filtering capabilities

================================================================================
"""

from typing import Optional, List, Dict
from fastapi import HTTPException, status
from datetime import datetime
from uuid import UUID
import logging

from app.database import (
    fetch_one, fetch_all, execute_query, DatabaseTransaction,
    fetch_one_tx, execute_query_tx
)
from app.schemas.development import (
    FeatureStatus, FeaturePriority, StepStatus,
    CreateFeatureRequest, UpdateFeatureRequest,
    CreateStepRequest, UpdateStepRequest,
    CreateCommentRequest
)

logger = logging.getLogger(__name__)


# ============================================================================
# FEATURE OPERATIONS
# ============================================================================


async def get_features_list(
    feature_status: Optional[FeatureStatus] = None,
    priority: Optional[FeaturePriority] = None,
    page: int = 1,
    limit: int = 50,
) -> Dict:
    """Get paginated list of features."""
    where_conditions = []
    params = []
    param_count = 1

    if feature_status:
        where_conditions.append(f"f.status = ${param_count}")
        params.append(feature_status.value)
        param_count += 1

    if priority:
        where_conditions.append(f"f.priority = ${param_count}")
        params.append(priority.value)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    # Get total count
    count_result = await fetch_one(f"SELECT COUNT(*) as total FROM features f {where_clause}", *params)
    total = count_result["total"] if count_result else 0

    # Get paginated results
    offset = (page - 1) * limit
    features_query = f"""
        SELECT
            f.id,
            f.title,
            f.description,
            f.status,
            f.priority,
            f.target_date,
            f.created_by_id::text,
            up.full_name as created_by_name,
            au.email as created_by_email,
            f.created_at,
            f.updated_at,
            COALESCE((SELECT COUNT(*) FROM feature_steps fs WHERE fs.feature_id = f.id), 0) as step_count,
            COALESCE((SELECT COUNT(*) FROM feature_steps fs WHERE fs.feature_id = f.id AND fs.status = 'done'), 0) as completed_steps,
            COALESCE((SELECT COUNT(*) FROM feature_comments fc WHERE fc.feature_id = f.id), 0) as comment_count
        FROM features f
        LEFT JOIN user_profiles up ON f.created_by_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        {where_clause}
        ORDER BY
            CASE f.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            f.created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """

    features = await fetch_all(features_query, *params, limit, offset)

    return {
        "features": features,
        "total": total,
        "page": page,
        "limit": limit,
    }


async def get_feature_by_id(feature_id: int) -> Dict:
    """Get a single feature with steps and comments."""
    feature_query = """
        SELECT
            f.id,
            f.title,
            f.description,
            f.status,
            f.priority,
            f.target_date,
            f.created_by_id::text,
            up.full_name as created_by_name,
            au.email as created_by_email,
            f.created_at,
            f.updated_at
        FROM features f
        LEFT JOIN user_profiles up ON f.created_by_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        WHERE f.id = $1
    """

    feature = await fetch_one(feature_query, feature_id)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with id {feature_id} not found"
        )

    # Get steps
    steps = await fetch_all(
        """
        SELECT id, feature_id, title, description, status, step_order, created_at, updated_at
        FROM feature_steps
        WHERE feature_id = $1
        ORDER BY step_order ASC, id ASC
        """,
        feature_id
    )

    # Get comments
    comments = await fetch_all(
        """
        SELECT
            fc.id,
            fc.feature_id,
            fc.user_id::text,
            up.full_name as user_name,
            au.email as user_email,
            fc.comment,
            fc.created_at,
            fc.updated_at
        FROM feature_comments fc
        LEFT JOIN user_profiles up ON fc.user_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        WHERE fc.feature_id = $1
        ORDER BY fc.created_at ASC
        """,
        feature_id
    )

    feature["steps"] = steps
    feature["comments"] = comments

    return feature


async def create_feature(request: CreateFeatureRequest, user_id: str) -> Dict:
    """Create a new feature. Admin only."""
    feature_id = await execute_query(
        """
        INSERT INTO features (title, description, priority, target_date, created_by_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        request.title,
        request.description,
        request.priority.value,
        request.target_date,
        UUID(user_id)
    )

    logger.info(f"Feature {feature_id} created by user {user_id}")
    return await get_feature_by_id(feature_id)


async def update_feature(feature_id: int, request: UpdateFeatureRequest) -> Dict:
    """Update a feature."""
    feature = await fetch_one("SELECT id FROM features WHERE id = $1", feature_id)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with id {feature_id} not found"
        )

    update_fields = []
    params = []
    param_count = 1

    if request.title is not None:
        update_fields.append(f"title = ${param_count}")
        params.append(request.title)
        param_count += 1

    if request.description is not None:
        update_fields.append(f"description = ${param_count}")
        params.append(request.description)
        param_count += 1

    if request.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(request.status.value)
        param_count += 1

    if request.priority is not None:
        update_fields.append(f"priority = ${param_count}")
        params.append(request.priority.value)
        param_count += 1

    if request.target_date is not None:
        update_fields.append(f"target_date = ${param_count}")
        params.append(request.target_date)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    params.append(feature_id)

    await execute_query(
        f"UPDATE features SET {', '.join(update_fields)} WHERE id = ${param_count}",
        *params
    )

    logger.info(f"Feature {feature_id} updated")
    return await get_feature_by_id(feature_id)


async def delete_feature(feature_id: int) -> Dict:
    """Delete a feature and all its steps/comments."""
    feature = await fetch_one("SELECT id FROM features WHERE id = $1", feature_id)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with id {feature_id} not found"
        )

    await execute_query("DELETE FROM features WHERE id = $1", feature_id)

    logger.info(f"Feature {feature_id} deleted")
    return {"message": "Feature deleted successfully"}


# ============================================================================
# STEP OPERATIONS
# ============================================================================


async def create_step(feature_id: int, request: CreateStepRequest) -> Dict:
    """Create a new step for a feature."""
    feature = await fetch_one("SELECT id FROM features WHERE id = $1", feature_id)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with id {feature_id} not found"
        )

    # Get max order if not provided
    step_order = request.step_order
    if step_order is None:
        max_order = await fetch_one(
            "SELECT COALESCE(MAX(step_order), 0) as max_order FROM feature_steps WHERE feature_id = $1",
            feature_id
        )
        step_order = max_order["max_order"] + 1

    step_id = await execute_query(
        """
        INSERT INTO feature_steps (feature_id, title, description, step_order)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        feature_id,
        request.title,
        request.description,
        step_order
    )

    logger.info(f"Step {step_id} created for feature {feature_id}")

    return await fetch_one(
        "SELECT id, feature_id, title, description, status, step_order, created_at, updated_at FROM feature_steps WHERE id = $1",
        step_id
    )


async def update_step(step_id: int, request: UpdateStepRequest) -> Dict:
    """Update a step."""
    step = await fetch_one("SELECT id, feature_id FROM feature_steps WHERE id = $1", step_id)

    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with id {step_id} not found"
        )

    update_fields = []
    params = []
    param_count = 1

    if request.title is not None:
        update_fields.append(f"title = ${param_count}")
        params.append(request.title)
        param_count += 1

    if request.description is not None:
        update_fields.append(f"description = ${param_count}")
        params.append(request.description)
        param_count += 1

    if request.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(request.status.value)
        param_count += 1

    if request.step_order is not None:
        update_fields.append(f"step_order = ${param_count}")
        params.append(request.step_order)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    params.append(step_id)

    await execute_query(
        f"UPDATE feature_steps SET {', '.join(update_fields)} WHERE id = ${param_count}",
        *params
    )

    logger.info(f"Step {step_id} updated")

    return await fetch_one(
        "SELECT id, feature_id, title, description, status, step_order, created_at, updated_at FROM feature_steps WHERE id = $1",
        step_id
    )


async def delete_step(step_id: int) -> Dict:
    """Delete a step."""
    step = await fetch_one("SELECT id FROM feature_steps WHERE id = $1", step_id)

    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with id {step_id} not found"
        )

    await execute_query("DELETE FROM feature_steps WHERE id = $1", step_id)

    logger.info(f"Step {step_id} deleted")
    return {"message": "Step deleted successfully"}


async def reorder_steps(feature_id: int, step_ids: List[int]) -> List[Dict]:
    """Reorder steps for a feature."""
    feature = await fetch_one("SELECT id FROM features WHERE id = $1", feature_id)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with id {feature_id} not found"
        )

    async with DatabaseTransaction() as conn:
        for order, step_id in enumerate(step_ids):
            await execute_query_tx(
                "UPDATE feature_steps SET step_order = $1 WHERE id = $2 AND feature_id = $3",
                order,
                step_id,
                feature_id,
                conn=conn
            )

    logger.info(f"Steps reordered for feature {feature_id}")

    return await fetch_all(
        "SELECT id, feature_id, title, description, status, step_order, created_at, updated_at FROM feature_steps WHERE feature_id = $1 ORDER BY step_order ASC",
        feature_id
    )


# ============================================================================
# COMMENT OPERATIONS
# ============================================================================


async def add_comment(feature_id: int, request: CreateCommentRequest, user_id: str) -> Dict:
    """Add a comment to a feature."""
    feature = await fetch_one("SELECT id FROM features WHERE id = $1", feature_id)

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with id {feature_id} not found"
        )

    comment_id = await execute_query(
        """
        INSERT INTO feature_comments (feature_id, user_id, comment)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        feature_id,
        UUID(user_id),
        request.comment
    )

    logger.info(f"Comment {comment_id} added to feature {feature_id}")

    return await fetch_one(
        """
        SELECT
            fc.id,
            fc.feature_id,
            fc.user_id::text,
            up.full_name as user_name,
            au.email as user_email,
            fc.comment,
            fc.created_at,
            fc.updated_at
        FROM feature_comments fc
        LEFT JOIN user_profiles up ON fc.user_id = up.id
        LEFT JOIN auth.users au ON au.id = up.id
        WHERE fc.id = $1
        """,
        comment_id
    )


async def delete_comment(comment_id: int, user_id: str, is_admin: bool) -> Dict:
    """Delete a comment."""
    comment = await fetch_one(
        "SELECT id, user_id::text FROM feature_comments WHERE id = $1",
        comment_id
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found"
        )

    if not is_admin and comment["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    await execute_query("DELETE FROM feature_comments WHERE id = $1", comment_id)

    logger.info(f"Comment {comment_id} deleted")
    return {"message": "Comment deleted successfully"}


# ============================================================================
# STATISTICS
# ============================================================================


async def get_feature_stats() -> Dict:
    """Get feature statistics."""
    status_query = """
        SELECT
            COUNT(*) as total_features,
            COUNT(*) FILTER (WHERE status = 'planned') as planned,
            COUNT(*) FILTER (WHERE status = 'in_development') as in_development,
            COUNT(*) FILTER (WHERE status = 'testing') as testing,
            COUNT(*) FILTER (WHERE status = 'completed') as completed,
            COUNT(*) FILTER (WHERE status = 'on_hold') as on_hold
        FROM features
    """
    status_stats = await fetch_one(status_query)

    # Get by priority
    priority_results = await fetch_all(
        "SELECT priority, COUNT(*) as count FROM features GROUP BY priority"
    )
    by_priority = {row["priority"]: row["count"] for row in priority_results}

    # Get step stats
    step_stats = await fetch_one(
        """
        SELECT
            COUNT(*) as total_steps,
            COUNT(*) FILTER (WHERE status = 'done') as completed_steps
        FROM feature_steps
        """
    )

    return {
        "total_features": status_stats["total_features"],
        "planned": status_stats["planned"],
        "in_development": status_stats["in_development"],
        "testing": status_stats["testing"],
        "completed": status_stats["completed"],
        "on_hold": status_stats["on_hold"],
        "by_priority": by_priority,
        "total_steps": step_stats["total_steps"],
        "completed_steps": step_stats["completed_steps"],
    }

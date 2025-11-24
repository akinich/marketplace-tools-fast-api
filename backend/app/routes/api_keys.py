"""
API Key Routes
File: backend/app/routes/api_keys.py
Description: API endpoints for API key management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.api_keys import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreatedResponse,
    APIKeyUsageResponse,
    AvailableScopesResponse
)
from app.services import api_key_service
from app.schemas.auth import CurrentUser
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# ============================================================================
# API KEY MANAGEMENT ROUTES
# ============================================================================


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all API keys for the current user.

    Returns:
        List of API key objects (without full key)
    """
    db = get_db()
    keys = await api_key_service.get_user_api_keys(db, current_user.id)

    logger.info(f"User {current_user.email} listed {len(keys)} API keys")
    return keys


@router.post("/", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new API key.

    **WARNING:** The full API key is only shown once in the response.
    Store it securely as it cannot be retrieved later.

    Args:
        request: API key creation parameters

    Returns:
        Created API key with full key (shown only once)

    Raises:
        400: If scopes are invalid
    """
    db = get_db()

    try:
        created = await api_key_service.create_api_key(
            db,
            user_id=current_user.id,
            name=request.name,
            scopes=request.scopes,
            description=request.description,
            expires_in_days=request.expires_in_days
        )

        logger.info(
            f"User {current_user.email} created API key '{request.name}' "
            f"with scopes: {', '.join(request.scopes)}"
        )

        return created

    except ValueError as e:
        logger.warning(f"Invalid API key creation attempt by {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{api_key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    api_key_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Revoke an API key.

    This deactivates the key immediately. The action cannot be undone.

    Args:
        api_key_id: ID of the API key to revoke

    Returns:
        Success message

    Raises:
        404: If API key not found or doesn't belong to user
    """
    db = get_db()
    success = await api_key_service.revoke_api_key(db, api_key_id, current_user.id)

    if not success:
        logger.warning(
            f"User {current_user.email} attempted to revoke non-existent or "
            f"unauthorized API key {api_key_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or you don't have permission to revoke it"
        )

    logger.info(f"User {current_user.email} revoked API key {api_key_id}")
    return {"message": "API key revoked successfully"}


@router.get("/{api_key_id}/usage", response_model=List[APIKeyUsageResponse])
async def get_api_key_usage(
    api_key_id: int,
    limit: int = 100,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get usage logs for an API key.

    Args:
        api_key_id: ID of the API key
        limit: Maximum number of log entries to return (default: 100, max: 1000)

    Returns:
        List of usage log entries

    Raises:
        404: If API key not found or doesn't belong to user
    """
    # Limit the limit to prevent abuse
    limit = min(limit, 1000)

    db = get_db()
    usage = await api_key_service.get_api_key_usage(
        db,
        api_key_id,
        current_user.id,
        limit
    )

    if usage is None or len(usage) == 0:
        # Check if key exists
        keys = await api_key_service.get_user_api_keys(db, current_user.id)
        key_exists = any(k['id'] == api_key_id for k in keys)

        if not key_exists:
            logger.warning(
                f"User {current_user.email} attempted to view usage for "
                f"non-existent or unauthorized API key {api_key_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or you don't have permission to view its usage"
            )

    logger.info(f"User {current_user.email} viewed usage for API key {api_key_id}")
    return usage if usage else []


# ============================================================================
# SCOPE INFORMATION ROUTES
# ============================================================================


@router.get("/scopes/available", response_model=AvailableScopesResponse)
async def get_available_scopes(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of all available API key scopes.

    Returns:
        Dictionary with list of available scopes
    """
    return {"scopes": api_key_service.AVAILABLE_SCOPES}


# ============================================================================
# ADMIN ROUTES
# ============================================================================


@router.get("/admin/all", response_model=List[APIKeyResponse])
async def list_all_api_keys(
    admin: CurrentUser = Depends(require_admin)
):
    """
    (Admin Only) List all API keys in the system.

    Returns:
        List of all API keys from all users
    """
    db = get_db()

    keys = await db.fetch(
        """
        SELECT
            ak.id, ak.user_id, ak.key_prefix, ak.name, ak.description,
            ak.scopes, ak.is_active, ak.expires_at, ak.last_used_at,
            ak.created_at, ak.revoked_at,
            up.email as user_email
        FROM api_keys ak
        JOIN user_profiles up ON ak.user_id = up.id
        ORDER BY ak.created_at DESC
        """
    )

    logger.info(f"Admin {admin.email} listed all {len(keys)} API keys")
    return [dict(k) for k in keys]


@router.delete("/admin/{api_key_id}", status_code=status.HTTP_200_OK)
async def admin_revoke_api_key(
    api_key_id: int,
    admin: CurrentUser = Depends(require_admin)
):
    """
    (Admin Only) Revoke any user's API key.

    Args:
        api_key_id: ID of the API key to revoke

    Returns:
        Success message

    Raises:
        404: If API key not found
    """
    db = get_db()

    result = await db.execute(
        """
        UPDATE api_keys
        SET is_active = false, revoked_at = NOW()
        WHERE id = $1
        """,
        api_key_id
    )

    if result == "UPDATE 0":
        logger.warning(f"Admin {admin.email} attempted to revoke non-existent API key {api_key_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    logger.info(f"Admin {admin.email} revoked API key {api_key_id}")
    return {"message": "API key revoked successfully"}

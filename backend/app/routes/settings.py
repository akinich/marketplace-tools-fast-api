"""
================================================================================
Farm Management System - Settings & Configuration Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-22

Changelog:
----------
v1.0.0 (2025-11-22):
  - Initial settings management endpoints
  - CRUD operations for system settings
  - Settings by category
  - Audit log tracking
  - Caching support
  - Admin-only access

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import logging
import json

from app.schemas.auth import CurrentUser
from app.auth.dependencies import require_admin
from app.models.settings import (
    SystemSettingResponse,
    SettingUpdateRequest,
    SettingsByCategoryResponse,
    SettingsAuditLogResponse
)
from app.services import settings_service
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _convert_setting_row(row: Dict) -> Dict:
    """Convert database row to proper format for Pydantic validation"""
    result = dict(row)

    # Convert validation_rules from JSONB string to dict
    if 'validation_rules' in result and result['validation_rules']:
        if isinstance(result['validation_rules'], str):
            result['validation_rules'] = json.loads(result['validation_rules'])
        elif result['validation_rules'] == '{}':
            result['validation_rules'] = {}
    else:
        result['validation_rules'] = {}

    # Convert updated_by UUID to string
    if 'updated_by' in result and result['updated_by']:
        result['updated_by'] = str(result['updated_by'])

    return result


def _convert_audit_log_row(row: Dict) -> Dict:
    """Convert audit log database row to proper format"""
    result = dict(row)

    # Ensure changed_by is a string (could be None)
    if 'changed_by' in result and result['changed_by']:
        result['changed_by'] = str(result['changed_by'])
    else:
        result['changed_by'] = 'Unknown'

    return result


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================


@router.get(
    "/",
    response_model=List[SystemSettingResponse],
    summary="Get All Settings",
    description="Get all system settings (Admin only)"
)
async def get_all_settings(
    current_user: CurrentUser = Depends(require_admin),
):
    """Get all system settings (Admin only)"""
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id, setting_key, setting_value, data_type, category,
                    description, validation_rules, is_public, is_encrypted,
                    updated_by, created_at, updated_at
                FROM system_settings
                ORDER BY category, setting_key
                """
            )
            return [_convert_setting_row(dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch settings"
        )


@router.get(
    "/public",
    response_model=Dict[str, Any],
    summary="Get Public Settings",
    description="Get public settings (accessible to all authenticated users)"
)
async def get_public_settings(
    current_user: CurrentUser = Depends(require_admin),
):
    """Get public settings (accessible to all authenticated users)"""
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            return await settings_service.get_public_settings(conn)
    except Exception as e:
        logger.error(f"Failed to fetch public settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch public settings"
        )


@router.get(
    "/categories",
    response_model=List[str],
    summary="Get Setting Categories",
    description="Get list of all setting categories"
)
async def get_categories(
    current_user: CurrentUser = Depends(require_admin),
):
    """Get list of setting categories"""
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM system_settings ORDER BY category"
            )
            return [row['category'] for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )


@router.get(
    "/category/{category}",
    response_model=List[SystemSettingResponse],
    summary="Get Settings By Category",
    description="Get all settings in a specific category"
)
async def get_settings_by_category(
    category: str,
    current_user: CurrentUser = Depends(require_admin),
):
    """Get all settings in a specific category"""
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            settings = await settings_service.get_settings_by_category(conn, category)
            return [_convert_setting_row(s) for s in settings]
    except Exception as e:
        logger.error(f"Failed to fetch settings for category {category}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settings for category: {category}"
        )


@router.put(
    "/{setting_key}",
    response_model=SystemSettingResponse,
    summary="Update Setting",
    description="Update a setting value with validation"
)
async def update_setting(
    setting_key: str,
    request: SettingUpdateRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """Update a setting value"""
    logger.info(f"[SETTINGS API] Received update request for setting: {setting_key}")
    logger.info(f"[SETTINGS API] Request value: {request.setting_value}, User: {current_user.email}")

    try:
        pool = get_db()
        async with pool.acquire() as conn:
            updated = await settings_service.update_setting(
                conn,
                setting_key,
                request.setting_value,
                current_user.id
            )
            logger.info(f"[SETTINGS API] ✅ Setting '{setting_key}' successfully updated by user {current_user.email}")
            return _convert_setting_row(updated)
    except ValueError as e:
        logger.warning(f"[SETTINGS API] ⚠️ Validation error updating setting {setting_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[SETTINGS API] ❌ Failed to update setting {setting_key}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {setting_key}"
        )


@router.get(
    "/audit-log",
    response_model=List[SettingsAuditLogResponse],
    summary="Get Audit Log",
    description="Get settings change audit log"
)
async def get_audit_log(
    setting_key: Optional[str] = None,
    limit: int = 100,
    current_user: CurrentUser = Depends(require_admin),
):
    """Get settings change audit log"""
    try:
        pool = get_db()
        async with pool.acquire() as conn:
            logs = await settings_service.get_audit_log(conn, setting_key, limit)
            return [_convert_audit_log_row(log) for log in logs]
    except Exception as e:
        logger.error(f"Failed to fetch audit log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch audit log"
        )

"""
================================================================================
Farm Management System - Security Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-21

Endpoints:
- GET /security/sessions - Get user's active sessions
- DELETE /security/sessions/{id} - Revoke a session
- DELETE /security/sessions - Revoke all other sessions
- GET /security/login-history - Get user's login history
- GET /security/admin/sessions - Admin: Get all sessions
- GET /security/admin/login-history - Admin: Get all login history
- DELETE /security/admin/sessions/{id} - Admin: Revoke any session
- GET /security/admin/stats - Admin: Security statistics
================================================================================
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.schemas.auth import CurrentUser, ErrorResponse
from app.auth.dependencies import get_current_user, require_admin
from app.services import security_service

router = APIRouter()


# ============================================================================
# USER ENDPOINTS
# ============================================================================


@router.get(
    "/sessions",
    summary="Get My Sessions",
    description="Get all active sessions for the current user",
)
async def get_my_sessions(current_user: CurrentUser = Depends(get_current_user)):
    """Get current user's active sessions."""
    sessions = await security_service.get_user_sessions(current_user.id)
    return {"sessions": sessions}


@router.delete(
    "/sessions/{session_id}",
    summary="Revoke Session",
    description="Revoke a specific session",
)
async def revoke_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Revoke a specific session."""
    return await security_service.revoke_session(session_id, current_user.id)


@router.delete(
    "/sessions",
    summary="Revoke All Other Sessions",
    description="Revoke all sessions except the current one",
)
async def revoke_all_my_sessions(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Revoke all other sessions for current user."""
    return await security_service.revoke_all_user_sessions(
        current_user.id,
        current_user.id,
        exclude_current=None  # In production, pass current session ID
    )


@router.get(
    "/login-history",
    summary="Get My Login History",
    description="Get login history for the current user",
)
async def get_my_login_history(
    limit: int = Query(20, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get current user's login history."""
    history = await security_service.get_user_login_history(current_user.id, limit)
    return {"history": history}


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================


@router.get(
    "/admin/sessions",
    summary="Get All Sessions (Admin)",
    description="Admin: Get all active sessions across all users",
)
async def get_all_sessions(admin: CurrentUser = Depends(require_admin)):
    """Admin: Get all active sessions."""
    sessions = await security_service.get_all_sessions_admin()
    return {"sessions": sessions}


@router.delete(
    "/admin/sessions/{session_id}",
    summary="Revoke Any Session (Admin)",
    description="Admin: Revoke any user's session",
)
async def admin_revoke_session(
    session_id: str,
    admin: CurrentUser = Depends(require_admin),
):
    """Admin: Revoke any session."""
    return await security_service.revoke_session(session_id, admin.id)


@router.delete(
    "/admin/users/{user_id}/sessions",
    summary="Revoke All User Sessions (Admin)",
    description="Admin: Revoke all sessions for a specific user",
)
async def admin_revoke_user_sessions(
    user_id: str,
    admin: CurrentUser = Depends(require_admin),
):
    """Admin: Revoke all sessions for a user."""
    return await security_service.revoke_all_user_sessions(user_id, admin.id)


@router.get(
    "/admin/login-history",
    summary="Get All Login History (Admin)",
    description="Admin: Get login history across all users",
)
async def get_all_login_history(
    limit: int = Query(50, le=200),
    status_filter: Optional[str] = Query(None, description="Filter by status: success, failed, locked"),
    admin: CurrentUser = Depends(require_admin),
):
    """Admin: Get all login history."""
    history = await security_service.get_all_login_history_admin(limit, status_filter)
    return {"history": history}


@router.get(
    "/admin/stats",
    summary="Get Security Stats (Admin)",
    description="Admin: Get security statistics",
)
async def get_security_stats(admin: CurrentUser = Depends(require_admin)):
    """Admin: Get security statistics."""
    stats = await security_service.get_security_stats()
    return stats

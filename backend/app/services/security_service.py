"""
================================================================================
Farm Management System - Security Service
================================================================================
Version: 1.0.0
Last Updated: 2025-11-21

Features:
- Active sessions management
- Login history tracking
- Rate limiting helpers
================================================================================
"""

from typing import Optional, Dict, List
from fastapi import HTTPException, status, Request
import logging
import hashlib
from datetime import datetime, timedelta

from app.database import fetch_one, fetch_all, execute_query
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


def hash_token(token: str) -> str:
    """Create a hash of the refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(
    user_id: str,
    refresh_token: str,
    request: Request,
    user_role: str = "User",
    expires_days: int = 7
) -> Dict:
    """
    Create a new session record when user logs in.

    Session limits by role:
    - Admin: 5 sessions max
    - User: 1 session only (single session)

    When limit exceeded, oldest session(s) are automatically revoked.
    """
    try:
        # Role-based session limits
        MAX_SESSIONS = {
            "Admin": 5,
            "User": 1
        }
        max_sessions = MAX_SESSIONS.get(user_role, 1)

        # Get current active session count
        current_sessions = await fetch_all(
            """
            SELECT id, created_at
            FROM user_sessions
            WHERE user_id = $1 AND is_active = TRUE AND expires_at > NOW()
            ORDER BY created_at ASC
            """,
            user_id
        )

        # If at or over limit, revoke oldest sessions
        if len(current_sessions) >= max_sessions:
            sessions_to_revoke = len(current_sessions) - max_sessions + 1
            sessions_to_delete = current_sessions[:sessions_to_revoke]

            for session in sessions_to_delete:
                await execute_query(
                    """
                    UPDATE user_sessions
                    SET is_active = FALSE, revoked_at = NOW(), revoked_by = $1
                    WHERE id = $2
                    """,
                    user_id,  # User revoked their own old session
                    session["id"]
                )

            logger.info(f"Revoked {sessions_to_revoke} old session(s) for user {user_id} ({user_role})")

        # Create new session
        token_hash = hash_token(refresh_token)
        device_info = request.headers.get("user-agent", "Unknown")
        ip_address = request.client.host if request.client else None
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # Simple location placeholder - in production, use IP geolocation API
        location = "Unknown"

        session = await fetch_one(
            """
            INSERT INTO user_sessions (user_id, refresh_token_hash, device_info, ip_address, location, expires_at)
            VALUES ($1, $2, $3, $4::inet, $5, $6)
            RETURNING id, device_info, ip_address, location, created_at
            """,
            user_id,
            token_hash,
            device_info,
            ip_address,
            location,
            expires_at
        )

        return session

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return None


async def get_user_sessions(user_id: str) -> List[Dict]:
    """
    Get all active sessions for a user.
    """
    sessions = await fetch_all(
        """
        SELECT
            id,
            device_info,
            ip_address::text,
            location,
            created_at,
            last_activity,
            is_active
        FROM user_sessions
        WHERE user_id = $1 AND is_active = TRUE AND expires_at > NOW()
        ORDER BY last_activity DESC
        """,
        user_id
    )
    return sessions or []


async def get_all_sessions_admin() -> List[Dict]:
    """
    Admin: Get all active sessions across all users.
    """
    sessions = await fetch_all(
        """
        SELECT
            us.id,
            us.user_id,
            au.email as user_email,
            up.full_name as user_name,
            us.device_info,
            us.ip_address::text,
            us.location,
            us.created_at,
            us.last_activity,
            us.is_active
        FROM user_sessions us
        JOIN user_profiles up ON up.id = us.user_id
        JOIN auth.users au ON au.id = us.user_id
        WHERE us.is_active = TRUE AND us.expires_at > NOW()
        ORDER BY us.last_activity DESC
        LIMIT 100
        """
    )
    return sessions or []


async def revoke_session(session_id: str, revoked_by: str) -> Dict:
    """
    Revoke a specific session.
    """
    result = await execute_query(
        """
        UPDATE user_sessions
        SET is_active = FALSE, revoked_at = NOW(), revoked_by = $2
        WHERE id = $1
        RETURNING id
        """,
        session_id,
        revoked_by
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session revoked successfully"}


async def revoke_all_user_sessions(user_id: str, revoked_by: str, exclude_current: str = None) -> Dict:
    """
    Revoke all sessions for a user (optionally excluding current session).
    """
    if exclude_current:
        await execute_query(
            """
            UPDATE user_sessions
            SET is_active = FALSE, revoked_at = NOW(), revoked_by = $2
            WHERE user_id = $1 AND is_active = TRUE AND id != $3
            """,
            user_id,
            revoked_by,
            exclude_current
        )
    else:
        await execute_query(
            """
            UPDATE user_sessions
            SET is_active = FALSE, revoked_at = NOW(), revoked_by = $2
            WHERE user_id = $1 AND is_active = TRUE
            """,
            user_id,
            revoked_by
        )

    return {"message": "All sessions revoked successfully"}


# ============================================================================
# LOGIN HISTORY
# ============================================================================


async def record_login_attempt(
    user_id: str,
    request: Request,
    status: str,
    failure_reason: str = None
) -> Dict:
    """
    Record a login attempt (success or failure).
    """
    try:
        device_info = request.headers.get("user-agent", "Unknown")
        ip_address = request.client.host if request.client else None
        location = "Unknown"  # Placeholder for IP geolocation

        # Check if this is a new device/location
        is_new_device = False
        is_new_location = False

        if user_id and status == "success":
            # Check previous logins for this user
            previous = await fetch_one(
                """
                SELECT device_info, ip_address::text, location
                FROM login_history
                WHERE user_id = $1 AND login_status = 'success'
                ORDER BY login_at DESC
                LIMIT 1
                """,
                user_id
            )

            if previous:
                if previous["device_info"] != device_info:
                    is_new_device = True
                if previous["ip_address"] != ip_address:
                    is_new_location = True

        await execute_query(
            """
            INSERT INTO login_history
            (user_id, ip_address, device_info, location, login_status, failure_reason, is_new_device, is_new_location)
            VALUES ($1, $2::inet, $3, $4, $5, $6, $7, $8)
            """,
            user_id,
            ip_address,
            device_info,
            location,
            status,
            failure_reason,
            is_new_device,
            is_new_location
        )

        return {"is_new_device": is_new_device, "is_new_location": is_new_location}

    except Exception as e:
        logger.error(f"Failed to record login attempt: {e}")
        return {}


async def get_user_login_history(user_id: str, limit: int = 20) -> List[Dict]:
    """
    Get login history for a specific user.
    """
    history = await fetch_all(
        """
        SELECT
            id,
            login_at,
            ip_address::text,
            device_info,
            location,
            login_status,
            failure_reason,
            is_new_device,
            is_new_location
        FROM login_history
        WHERE user_id = $1
        ORDER BY login_at DESC
        LIMIT $2
        """,
        user_id,
        limit
    )
    return history or []


async def get_all_login_history_admin(
    limit: int = 50,
    status_filter: str = None
) -> List[Dict]:
    """
    Admin: Get login history across all users.
    """
    if status_filter:
        history = await fetch_all(
            """
            SELECT
                lh.id,
                lh.user_id,
                au.email as user_email,
                up.full_name as user_name,
                lh.login_at,
                lh.ip_address::text,
                lh.device_info,
                lh.location,
                lh.login_status,
                lh.failure_reason,
                lh.is_new_device,
                lh.is_new_location
            FROM login_history lh
            LEFT JOIN user_profiles up ON up.id = lh.user_id
            LEFT JOIN auth.users au ON au.id = lh.user_id
            WHERE lh.login_status = $1
            ORDER BY lh.login_at DESC
            LIMIT $2
            """,
            status_filter,
            limit
        )
    else:
        history = await fetch_all(
            """
            SELECT
                lh.id,
                lh.user_id,
                au.email as user_email,
                up.full_name as user_name,
                lh.login_at,
                lh.ip_address::text,
                lh.device_info,
                lh.location,
                lh.login_status,
                lh.failure_reason,
                lh.is_new_device,
                lh.is_new_location
            FROM login_history lh
            LEFT JOIN user_profiles up ON up.id = lh.user_id
            LEFT JOIN auth.users au ON au.id = lh.user_id
            ORDER BY lh.login_at DESC
            LIMIT $1
            """,
            limit
        )
    return history or []


async def get_security_stats() -> Dict:
    """
    Get security statistics for admin dashboard.
    """
    stats = await fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM user_sessions WHERE is_active = TRUE AND expires_at > NOW()) as active_sessions,
            (SELECT COUNT(*) FROM login_history WHERE login_at > NOW() - INTERVAL '24 hours' AND login_status = 'success') as logins_24h,
            (SELECT COUNT(*) FROM login_history WHERE login_at > NOW() - INTERVAL '24 hours' AND login_status = 'failed') as failed_logins_24h,
            (SELECT COUNT(*) FROM login_history WHERE login_at > NOW() - INTERVAL '24 hours' AND login_status = 'locked') as lockouts_24h,
            (SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE is_active = TRUE AND expires_at > NOW()) as users_with_sessions
        """
    )
    return dict(stats) if stats else {}

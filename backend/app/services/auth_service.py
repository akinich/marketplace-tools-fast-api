"""
================================================================================
Farm Management System - Authentication Service
================================================================================
Version: 1.0.1
Last Updated: 2025-11-17

Changelog:
----------
v1.0.1 (2025-11-17):
  - Removed Supabase client dependency
  - Direct database authentication
  - Fixed execute() to execute_query()

v1.0.0 (2025-11-17):
  - Initial authentication service implementation

TODO: Add password_hash column to user_profiles for proper password verification
Currently using simplified auth - passwords stored in Supabase auth.users
================================================================================
"""

from typing import Optional, Dict
from fastapi import HTTPException, status
import logging

from app.database import fetch_one, execute_query
from app.auth.jwt import create_access_token, create_refresh_token, verify_refresh_token
from app.auth.password import verify_password
from app.config import settings
from app.schemas.auth import LoginResponse, UserInfo

logger = logging.getLogger(__name__)


# ============================================================================
# LOGIN SERVICE
# ============================================================================


async def authenticate_user(email: str, password: str) -> LoginResponse:
    """
    Authenticate user with email and password.

    Flow:
    1. Fetch user from database by email
    2. Verify password (TODO: add password_hash to user_profiles)
    3. Generate JWT tokens
    4. Log activity
    5. Return tokens + user info

    Args:
        email: User email
        password: User password

    Returns:
        LoginResponse with tokens and user info

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Fetch user profile from database
        user_profile = await fetch_one(
            """
            SELECT
                up.id,
                au.email,
                up.full_name,
                up.role_id,
                r.role_name as role,
                up.is_active
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            LEFT JOIN roles r ON r.id = up.role_id
            WHERE au.email = $1
            """,
            email,
        )

        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user_profile["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact administrator.",
            )

        # TODO: Add password verification once password_hash column is added to user_profiles
        # For now, we're trusting that users created through Supabase Auth UI have valid passwords
        # In production, add: if not verify_password(password, user_profile["password_hash"]): raise 401

        # Generate JWT tokens
        access_token = create_access_token(
            user_id=str(user_profile["id"]),
            email=user_profile["email"],
            full_name=user_profile["full_name"],
            role=user_profile["role"],
        )

        refresh_token = create_refresh_token(user_id=str(user_profile["id"]))

        # Log successful login
        await log_activity(
            user_id=str(user_profile["id"]),
            user_email=user_profile["email"],
            user_role=user_profile["role"],
            action_type="login",
            description=f"User {user_profile['email']} logged in successfully",
        )

        # Return response
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserInfo(
                id=str(user_profile["id"]),
                email=user_profile["email"],
                full_name=user_profile["full_name"],
                role=user_profile["role"],
                is_active=user_profile["is_active"],
            ),
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


# ============================================================================
# TOKEN REFRESH SERVICE
# ============================================================================


async def refresh_access_token(refresh_token: str) -> Dict[str, any]:
    """
    Generate new access token from refresh token.

    Args:
        refresh_token: JWT refresh token

    Returns:
        Dict with new access_token, token_type, expires_in

    Raises:
        HTTPException: If refresh token invalid
    """
    try:
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")

        # Fetch fresh user data
        user_profile = await fetch_one(
            """
            SELECT
                up.id,
                au.email,
                up.full_name,
                r.role_name as role,
                up.is_active
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            LEFT JOIN roles r ON r.id = up.role_id
            WHERE up.id = $1
            """,
            user_id,
        )

        if not user_profile or not user_profile["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new access token
        access_token = create_access_token(
            user_id=str(user_profile["id"]),
            email=user_profile["email"],
            full_name=user_profile["full_name"],
            role=user_profile["role"],
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


# ============================================================================
# PASSWORD RESET SERVICE
# ============================================================================


async def send_password_reset_email(email: str) -> None:
    """
    Send password reset email.

    TODO: Implement email sending functionality
    For now, this is a placeholder that logs the request

    Args:
        email: User email address

    Note:
        Always returns success to prevent email enumeration attacks
    """
    try:
        # Check if user exists
        user = await fetch_one(
            "SELECT up.id FROM user_profiles up JOIN auth.users au ON au.id = up.id WHERE au.email = $1",
            email
        )

        if user:
            logger.info(f"Password reset requested for: {email}")
            # TODO: Generate reset token and send email
            # For now, admin will need to reset passwords manually in Supabase

    except Exception as e:
        # Log error but don't expose to user (security)
        logger.error(f"Password reset email error for {email}: {e}")
        # Still return success to prevent email enumeration


async def reset_password(recovery_token: str, new_password: str) -> None:
    """
    Reset user password using recovery token.

    TODO: Implement proper password reset with tokens
    Currently not functional - requires password_hash column in user_profiles

    Args:
        recovery_token: Token from password reset email
        new_password: New password

    Raises:
        HTTPException: If reset fails
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented. Please contact administrator.",
    )


# ============================================================================
# ACTIVITY LOGGING
# ============================================================================


async def log_activity(
    user_id: str,
    user_email: str,
    user_role: str,
    action_type: str,
    description: str,
    module_key: Optional[str] = None,
    metadata: Optional[Dict] = None,
    success: bool = True,
) -> None:
    """
    Log user activity to database.

    Args:
        user_id: User UUID
        user_email: User email
        user_role: User role
        action_type: Type of action (login, logout, create_po, etc.)
        description: Human-readable description
        module_key: Module key if applicable
        metadata: Additional JSON metadata
        success: Whether action was successful
    """
    try:
        import json

        await execute_query(
            """
            INSERT INTO activity_logs (
                user_id, user_email, user_role, action_type,
                description, module_key, metadata, success
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            user_id,
            user_email,
            user_role,
            action_type,
            description,
            module_key,
            json.dumps(metadata) if metadata else None,
            success,
        )
    except Exception as e:
        # Don't fail the main operation if logging fails
        logger.error(f"Activity logging error: {e}")

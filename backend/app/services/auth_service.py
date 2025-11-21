"""
================================================================================
Farm Management System - Authentication Service
================================================================================
Version: 1.3.0
Last Updated: 2025-11-21

Changelog:
----------
v1.3.0 (2025-11-21):
  - Added account lockout after 5 failed login attempts
  - Added 15-minute lockout duration
  - Added must_change_password flag support
  - Added change_password endpoint for logged-in users
  - Added admin unlock account functionality

v1.2.0 (2025-11-18):
  - CRITICAL SECURITY FIX: Implemented proper password verification
  - Added password_hash column to user query
  - Enabled bcrypt password verification on login
  - Prevents authentication bypass vulnerability

v1.1.0 (2025-11-17):
  - Implemented full password reset flow with Supabase Auth
  - Added token generation and storage in database
  - Integrated Supabase email sending for password reset
  - Added password reset token verification
  - Added password update with bcrypt hashing

v1.0.1 (2025-11-17):
  - Removed Supabase client dependency
  - Direct database authentication
  - Fixed execute() to execute_query()

v1.0.0 (2025-11-17):
  - Initial authentication service implementation
================================================================================
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import logging
import secrets
from datetime import datetime, timedelta

from app.database import fetch_one, execute_query, fetch_all
from app.auth.jwt import create_access_token, create_refresh_token, verify_refresh_token
from app.auth.password import verify_password, hash_password, validate_password_strength
from app.config import settings
from app.schemas.auth import LoginResponse, UserInfo
from app.utils.supabase_client import get_supabase_client

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

logger = logging.getLogger(__name__)


# ============================================================================
# LOGIN SERVICE
# ============================================================================


async def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticate user with email and password.

    Flow:
    1. Fetch user from database by email
    2. Check account lockout status
    3. Verify password (increment failed attempts on failure)
    4. Reset failed attempts on success
    5. Generate JWT tokens
    6. Log activity
    7. Return tokens + user info + must_change_password flag

    Args:
        email: User email
        password: User password

    Returns:
        Dict with tokens, user info, and must_change_password flag

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
                up.is_active,
                up.password_hash,
                up.failed_login_attempts,
                up.locked_until,
                up.must_change_password
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

        # Check account lockout
        locked_until = user_profile.get("locked_until")
        if locked_until and locked_until > datetime.utcnow():
            remaining_minutes = int((locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked due to too many failed login attempts. Try again in {remaining_minutes} minutes.",
            )

        # Verify password
        if not user_profile.get("password_hash"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not fully configured. Please use password reset.",
            )

        if not verify_password(password, user_profile["password_hash"]):
            # Increment failed login attempts
            failed_attempts = (user_profile.get("failed_login_attempts") or 0) + 1

            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                # Lock the account
                lock_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                await execute_query(
                    """
                    UPDATE user_profiles
                    SET failed_login_attempts = $1, locked_until = $2, updated_at = NOW()
                    WHERE id = $3
                    """,
                    failed_attempts,
                    lock_until,
                    user_profile["id"],
                )
                logger.warning(f"Account locked for user {email} after {failed_attempts} failed attempts")
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked due to {MAX_FAILED_ATTEMPTS} failed login attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes.",
                )
            else:
                # Just increment counter
                await execute_query(
                    """
                    UPDATE user_profiles
                    SET failed_login_attempts = $1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    failed_attempts,
                    user_profile["id"],
                )
                remaining = MAX_FAILED_ATTEMPTS - failed_attempts
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid email or password. {remaining} attempts remaining before account lockout.",
                )

        # Reset failed attempts on successful login
        await execute_query(
            """
            UPDATE user_profiles
            SET failed_login_attempts = 0, locked_until = NULL, updated_at = NOW()
            WHERE id = $1
            """,
            user_profile["id"],
        )

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

        # Return response with must_change_password flag
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "must_change_password": user_profile.get("must_change_password", False),
            "user": {
                "id": str(user_profile["id"]),
                "email": user_profile["email"],
                "full_name": user_profile["full_name"],
                "role": user_profile["role"],
                "is_active": user_profile["is_active"],
            },
        }

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


async def send_password_reset_email(email: str) -> Dict[str, str]:
    """
    Send password reset email using Supabase Auth.

    Args:
        email: User email address

    Returns:
        Dict with status message

    Note:
        Always returns success to prevent email enumeration attacks
    """
    try:
        # Check if user exists in our database
        user = await fetch_one(
            "SELECT up.id, au.email FROM user_profiles up JOIN auth.users au ON au.id = up.id WHERE au.email = $1 AND up.is_active = TRUE",
            email
        )

        if user:
            # Use Supabase Auth to send password reset email
            supabase = get_supabase_client()

            # Supabase will send the email with the configured template
            response = supabase.auth.reset_password_for_email(
                email,
                {
                    "redirect_to": f"{settings.FRONTEND_URL}/reset-password"
                }
            )

            logger.info(f"Password reset email sent to: {email}")

            # Generate our own token for additional tracking (optional)
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)

            # Store token in database
            await execute_query(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES ($1, $2, $3)
                """,
                user['id'],
                token,
                expires_at
            )

            logger.info(f"Password reset token generated for user: {user['id']}")

        else:
            # User doesn't exist, but don't reveal this (security)
            logger.warning(f"Password reset attempted for non-existent/inactive user: {email}")

    except Exception as e:
        # Log error but don't expose to user (security)
        logger.error(f"Password reset email error for {email}: {e}")
        # Still return success to prevent email enumeration

    # Always return success to prevent email enumeration
    return {"message": "If your email exists in our system, you will receive a password reset link shortly."}


async def reset_password(recovery_token: str, new_password: str) -> Dict[str, str]:
    """
    Reset user password using Supabase recovery token.

    This endpoint is called from the frontend after user clicks the reset link.
    Supabase handles token validation, we just update the password hash in our system.

    Args:
        recovery_token: Access token from Supabase password reset email
        new_password: New password

    Returns:
        Success message

    Raises:
        HTTPException: If reset fails
    """
    try:
        # Verify the recovery token with Supabase
        supabase = get_supabase_client()

        # Get user from Supabase using the recovery token
        user_response = supabase.auth.get_user(recovery_token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        user_id = user_response.user.id
        email = user_response.user.email

        # Update password in Supabase Auth using admin API
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": new_password}
        )

        # Also update password_hash in user_profiles if column exists
        # This ensures consistency if we migrate away from Supabase Auth
        hashed_password = hash_password(new_password)

        await execute_query(
            """
            UPDATE user_profiles
            SET password_hash = $1, updated_at = NOW()
            WHERE id = $2
            """,
            hashed_password,
            user_id
        )

        # Mark any password reset tokens as used
        await execute_query(
            """
            UPDATE password_reset_tokens
            SET used = TRUE, used_at = NOW()
            WHERE user_id = $1 AND used = FALSE
            """,
            user_id
        )

        logger.info(f"Password reset successful for user: {email}")

        return {"message": "Password reset successful. You can now login with your new password."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password. Please request a new reset link."
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


# ============================================================================
# CHANGE PASSWORD SERVICE (for logged-in users)
# ============================================================================


async def change_password(user_id: str, current_password: str, new_password: str) -> Dict[str, str]:
    """
    Change password for authenticated user.

    Args:
        user_id: Current user's UUID
        current_password: Current password for verification
        new_password: New password

    Returns:
        Success message

    Raises:
        HTTPException: If change fails
    """
    try:
        # Fetch user's current password hash
        user = await fetch_one(
            """
            SELECT up.id, au.email, up.password_hash, up.must_change_password
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            WHERE up.id = $1
            """,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Validate new password strength
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Check new password is different from current
        if verify_password(new_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # Hash and update password
        new_hash = hash_password(new_password)
        await execute_query(
            """
            UPDATE user_profiles
            SET password_hash = $1, must_change_password = FALSE,
                last_password_change = NOW(), updated_at = NOW()
            WHERE id = $2
            """,
            new_hash,
            user_id
        )

        # Also update in Supabase Auth
        try:
            supabase = get_supabase_client()
            supabase.auth.admin.update_user_by_id(user_id, {"password": new_password})
        except Exception as e:
            logger.warning(f"Failed to update password in Supabase Auth: {e}")

        logger.info(f"Password changed successfully for user: {user['email']}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )


# ============================================================================
# ADMIN UNLOCK ACCOUNT SERVICE
# ============================================================================


async def admin_unlock_account(user_id: str) -> Dict[str, str]:
    """
    Admin function to unlock a locked user account.

    Args:
        user_id: UUID of user to unlock

    Returns:
        Success message

    Raises:
        HTTPException: If unlock fails
    """
    try:
        # Check user exists
        user = await fetch_one(
            """
            SELECT up.id, au.email, up.locked_until, up.failed_login_attempts
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            WHERE up.id = $1
            """,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Reset lockout fields
        await execute_query(
            """
            UPDATE user_profiles
            SET failed_login_attempts = 0, locked_until = NULL, updated_at = NOW()
            WHERE id = $1
            """,
            user_id
        )

        logger.info(f"Account unlocked by admin for user: {user['email']}")

        return {"message": f"Account unlocked successfully for {user['email']}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin unlock account error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while unlocking account"
        )


# ============================================================================
# USER PROFILE SERVICES
# ============================================================================


async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user profile with security information.

    Args:
        user_id: UUID of user

    Returns:
        User profile dict with security info
    """
    try:
        user = await fetch_one(
            """
            SELECT
                up.id, au.email, up.full_name, r.role_name as role,
                up.is_active, up.created_at, up.last_password_change
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            JOIN roles r ON r.id = up.role_id
            WHERE up.id = $1
            """,
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "last_password_change": user["last_password_change"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching profile"
        )


async def update_user_profile(
    user_id: str, full_name: str, user_email: str, user_role: str
) -> Dict[str, str]:
    """
    Update user profile (full name).

    Args:
        user_id: UUID of user
        full_name: New full name
        user_email: User email for logging
        user_role: User role for logging

    Returns:
        Success message with updated name
    """
    try:
        await execute_query(
            """
            UPDATE user_profiles
            SET full_name = $1, updated_at = NOW()
            WHERE id = $2
            """,
            full_name, user_id
        )

        # Log activity
        await log_activity(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            action_type="profile_update",
            description=f"User {user_email} updated their profile name",
        )

        logger.info(f"Profile updated for user: {user_email}")

        return {"message": "Profile updated successfully", "full_name": full_name}

    except Exception as e:
        logger.error(f"Update user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )

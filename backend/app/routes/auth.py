"""
================================================================================
Farm Management System - Authentication Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial authentication endpoints
  - POST /login - User login
  - POST /refresh - Refresh access token
  - POST /logout - User logout
  - POST /forgot-password - Request password reset
  - POST /reset-password - Reset password with token
  - GET /me - Get current user info

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    CurrentUser,
    ErrorResponse,
)
from app.services.auth_service import (
    authenticate_user,
    refresh_access_token,
    send_password_reset_email,
    reset_password,
    log_activity,
)
from app.auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter()


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
    },
    summary="User Login",
    description="Authenticate user with email and password. Returns JWT tokens.",
)
async def login(credentials: LoginRequest):
    """
    User login endpoint.

    - Validates email and password
    - Returns access token, refresh token, and user info
    - Logs successful login activity
    """
    try:
        response = await authenticate_user(credentials.email, credentials.password)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


# ============================================================================
# TOKEN REFRESH ENDPOINT
# ============================================================================


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
    },
    summary="Refresh Access Token",
    description="Generate new access token using refresh token.",
)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token endpoint.

    - Accepts refresh token
    - Returns new access token
    - Does not generate new refresh token
    """
    try:
        token_data = await refresh_access_token(request.refresh_token)
        return RefreshTokenResponse(**token_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


# ============================================================================
# LOGOUT ENDPOINT
# ============================================================================


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    summary="User Logout",
    description="Logout current user. Client should discard tokens.",
)
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """
    User logout endpoint.

    - Logs logout activity
    - Client should discard tokens (JWT is stateless)
    - Optional: Could implement token blacklist in future
    """
    try:
        # Log logout activity
        await log_activity(
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role,
            action_type="logout",
            description=f"User {current_user.email} logged out",
        )

        return LogoutResponse(message="Logged out successfully")

    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Still return success even if logging fails
        return LogoutResponse(message="Logged out successfully")


# ============================================================================
# FORGOT PASSWORD ENDPOINT
# ============================================================================


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password reset email sent (if account exists)"},
    },
    summary="Request Password Reset",
    description="Send password reset email to user. Always returns success to prevent email enumeration.",
)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Forgot password endpoint.

    - Sends password reset email via Supabase Auth
    - Always returns success (security: prevent email enumeration)
    - User receives email with reset link
    """
    try:
        await send_password_reset_email(request.email)
        return ForgotPasswordResponse(
            message="Password reset email sent if account exists"
        )
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        # Still return success to prevent email enumeration
        return ForgotPasswordResponse(
            message="Password reset email sent if account exists"
        )


# ============================================================================
# RESET PASSWORD ENDPOINT
# ============================================================================


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password reset successful"},
        400: {"model": ErrorResponse, "description": "Invalid or expired reset token"},
    },
    summary="Reset Password",
    description="Reset user password using recovery token from email.",
)
async def reset_password_endpoint(request: ResetPasswordRequest):
    """
    Reset password endpoint.

    - Uses recovery token from password reset email
    - Updates user password via Supabase Auth
    - User can then login with new password
    """
    try:
        await reset_password(request.recovery_token, request.new_password)
        return ResetPasswordResponse(message="Password reset successful")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed. Token may be invalid or expired.",
        )


# ============================================================================
# GET CURRENT USER ENDPOINT
# ============================================================================


@router.get(
    "/me",
    response_model=CurrentUser,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Current user info"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    summary="Get Current User",
    description="Get information about the currently authenticated user.",
)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user endpoint.

    - Returns current authenticated user information
    - Useful for frontend to verify token and get user details
    """
    return current_user

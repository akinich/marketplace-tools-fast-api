"""
================================================================================
Farm Management System - Authentication Routes
================================================================================
Version: 1.2.0
Last Updated: 2025-11-21

Changelog:
----------
v1.2.0 (2025-11-21):
  - Added GET /profile - Get user profile with security info
  - Added PUT /profile - Update user profile (full name)

v1.1.0 (2025-11-21):
  - Added POST /change-password - Change password for logged-in users
  - Login now returns must_change_password flag
  - Added 423 Locked response for account lockout

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
    ChangePasswordRequest,
    ChangePasswordResponse,
    CurrentUser,
    ErrorResponse,
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
)
from app.services.auth_service import (
    authenticate_user,
    refresh_access_token,
    send_password_reset_email,
    reset_password,
    change_password,
    log_activity,
    get_user_profile,
    update_user_profile,
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
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account inactive"},
        423: {"model": ErrorResponse, "description": "Account locked"},
    },
    summary="User Login",
    description="Authenticate user with email and password. Returns JWT tokens and must_change_password flag.",
)
async def login(credentials: LoginRequest):
    """
    User login endpoint.

    - Validates email and password
    - Returns access token, refresh token, user info, and must_change_password flag
    - Logs successful login activity
    - Returns 423 Locked if account is locked due to failed attempts
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


# ============================================================================
# CHANGE PASSWORD ENDPOINT
# ============================================================================


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password changed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid new password"},
        401: {"model": ErrorResponse, "description": "Current password incorrect"},
    },
    summary="Change Password",
    description="Change password for logged-in user. Requires current password.",
)
async def change_password_endpoint(
    request: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Change password endpoint for authenticated users.

    - Requires current password for verification
    - Validates new password strength
    - Clears must_change_password flag on success
    """
    try:
        result = await change_password(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return ChangePasswordResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password",
        )


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User profile retrieved"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    summary="Get User Profile",
    description="Get detailed profile information including security settings.",
)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get user profile with security information.

    - Returns full profile with created_at, last_password_change
    """
    try:
        profile = await get_user_profile(current_user.id)
        return UserProfileResponse(**profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching profile",
        )


@router.put(
    "/profile",
    response_model=UpdateProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    summary="Update User Profile",
    description="Update user profile information (full name).",
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update user profile.

    - Updates full_name
    - Logs activity
    """
    try:
        result = await update_user_profile(
            user_id=current_user.id,
            full_name=request.full_name,
            user_email=current_user.email,
            user_role=current_user.role,
        )
        return UpdateProfileResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile",
        )

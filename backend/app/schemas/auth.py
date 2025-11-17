"""
================================================================================
Farm Management System - Authentication Schemas
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial authentication Pydantic models
  - Login, logout, refresh token schemas
  - Password reset schemas
  - User response models

================================================================================
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


# ============================================================================
# LOGIN SCHEMAS
# ============================================================================


class LoginRequest(BaseModel):
    """Login request payload"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "SecurePass123!"}
        }


class UserInfo(BaseModel):
    """User information in auth responses"""

    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role (Admin/User)")
    is_active: bool = Field(..., description="Account active status")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "Admin",
                "is_active": True,
            }
        }


class LoginResponse(BaseModel):
    """Login success response"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserInfo = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 900,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "john.doe@example.com",
                    "full_name": "John Doe",
                    "role": "Admin",
                    "is_active": True,
                },
            }
        }


# ============================================================================
# TOKEN REFRESH SCHEMAS
# ============================================================================


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        json_schema_extra = {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }


class RefreshTokenResponse(BaseModel):
    """Refresh token response"""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 900,
            }
        }


# ============================================================================
# LOGOUT SCHEMA
# ============================================================================


class LogoutResponse(BaseModel):
    """Logout response"""

    message: str = Field(default="Logged out successfully")

    class Config:
        json_schema_extra = {"example": {"message": "Logged out successfully"}}


# ============================================================================
# PASSWORD RESET SCHEMAS
# ============================================================================


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""

    email: EmailStr = Field(..., description="User email address")

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class ForgotPasswordResponse(BaseModel):
    """Forgot password response"""

    message: str = Field(
        default="Password reset email sent if account exists",
        description="Generic success message for security",
    )

    class Config:
        json_schema_extra = {
            "example": {"message": "Password reset email sent if account exists"}
        }


class ResetPasswordRequest(BaseModel):
    """Reset password request"""

    recovery_token: str = Field(..., description="Password recovery token from email")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength"""
        from app.auth.password import validate_password_strength

        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "recovery_token": "supabase_recovery_token_from_email",
                "new_password": "NewSecurePass123!",
            }
        }


class ResetPasswordResponse(BaseModel):
    """Reset password response"""

    message: str = Field(default="Password reset successful")

    class Config:
        json_schema_extra = {"example": {"message": "Password reset successful"}}


# ============================================================================
# CURRENT USER SCHEMA
# ============================================================================


class CurrentUser(BaseModel):
    """Current authenticated user"""

    id: str
    email: str
    full_name: str
    role: str
    role_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# ERROR RESPONSES
# ============================================================================


class ErrorResponse(BaseModel):
    """Generic error response"""

    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {"example": {"detail": "Invalid credentials"}}

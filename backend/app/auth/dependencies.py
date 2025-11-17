"""
================================================================================
Farm Management System - Authentication Dependencies
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial authentication dependencies for FastAPI
  - Token extraction from Authorization header
  - Current user dependency
  - Admin-only dependency
  - Module access checking dependency

================================================================================
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import JWTError

from app.auth.jwt import verify_access_token
from app.database import get_db, fetch_one
from app.schemas.auth import CurrentUser
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# SECURITY SCHEME
# ============================================================================

# HTTP Bearer token scheme for Swagger UI
security = HTTPBearer()


# ============================================================================
# TOKEN EXTRACTION
# ============================================================================


async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        JWT token string

    Raises:
        HTTPException: If token is missing or invalid format
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


# ============================================================================
# CURRENT USER DEPENDENCY
# ============================================================================


async def get_current_user(token: str = Depends(get_token)) -> CurrentUser:
    """
    Get current authenticated user from JWT token.

    This dependency:
    1. Extracts token from Authorization header
    2. Verifies and decodes JWT token
    3. Fetches user from database
    4. Checks if user is active
    5. Returns CurrentUser object

    Usage:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.id}

    Args:
        token: JWT access token

    Returns:
        CurrentUser object

    Raises:
        HTTPException: If token invalid, expired, or user not found/inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify and decode token
        payload = verify_access_token(token)
        if payload is None:
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception

    # Fetch user from database
    db = get_db()
    user = await fetch_one(
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
        WHERE up.id = $1
        """,
        user_id,
    )

    if not user:
        logger.warning(f"User not found in database: {user_id}")
        raise credentials_exception

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator.",
        )

    return CurrentUser(**user)


# ============================================================================
# ADMIN-ONLY DEPENDENCY
# ============================================================================


async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Require admin role for route access.

    Usage:
        @router.post("/admin/users")
        async def create_user(admin: CurrentUser = Depends(require_admin)):
            # Only admins can access this

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. You do not have sufficient permissions.",
        )

    return current_user


# ============================================================================
# MODULE ACCESS DEPENDENCY
# ============================================================================


def require_module_access(module_key: str):
    """
    Factory function to create module access checker.

    Usage:
        @router.get("/inventory/items")
        async def get_items(user: CurrentUser = Depends(require_module_access("inventory"))):
            # Only users with inventory module access

    Args:
        module_key: Module key (e.g., "inventory", "biofloc")

    Returns:
        Dependency function that checks module access
    """

    async def check_module_access(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        """Check if user has access to specified module"""

        # Admins have access to all modules
        if current_user.role.lower() == "admin":
            return current_user

        # Check user's module permissions
        db = get_db()
        has_access = await fetch_one(
            """
            SELECT 1
            FROM user_module_permissions ump
            JOIN modules m ON m.id = ump.module_id
            WHERE ump.user_id = $1
              AND m.module_key = $2
              AND ump.can_access = TRUE
              AND m.is_active = TRUE
            """,
            current_user.id,
            module_key,
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to module: {module_key}. Please contact administrator.",
            )

        return current_user

    return check_module_access


# ============================================================================
# OPTIONAL USER DEPENDENCY
# ============================================================================


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """
    Get current user if token provided, otherwise None.
    Useful for endpoints that work with or without authentication.

    Usage:
        @router.get("/public-or-private")
        async def mixed_route(user: Optional[CurrentUser] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.full_name}"}
            return {"message": "Hello guest"}

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        CurrentUser if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials.credentials)
    except HTTPException:
        return None

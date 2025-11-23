"""
================================================================================
Farm Management System - Authentication Dependencies
================================================================================
Version: 1.3.0
Last Updated: 2025-11-22

Changelog:
----------
v1.3.0 (2025-11-22):
  - Added API key authentication support
  - New dependency: require_api_key for API key authentication
  - New dependency: require_api_key_scope for scope-based authorization
  - New dependency: get_current_user_or_api_key for dual auth support
  - Integration with API key service for verification and logging

v1.2.0 (2025-11-17):
  - CRITICAL: Added missing role_id field to CurrentUser initialization
  - Fixed Pydantic validation error for role_id field requirement

v1.1.0 (2025-11-17):
  - CRITICAL: Fixed UUID to string conversion for Pydantic validation
  - asyncpg returns UUID objects, Pydantic expects strings
  - Added explicit str() conversion for user ID field

v1.0.0 (2025-11-17):
  - Initial authentication dependencies for FastAPI
  - Token extraction from Authorization header
  - Current user dependency
  - Admin-only dependency
  - Module access checking dependency

================================================================================
"""

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import JWTError

from app.auth.jwt import verify_access_token
from app.database import get_db, fetch_one
from app.schemas.auth import CurrentUser
from app.services import api_key_service
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
    5. **Validates user has at least one active session**
    6. Returns CurrentUser object

    Usage:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.id}

    Args:
        token: JWT access token

    Returns:
        CurrentUser object

    Raises:
        HTTPException: If token invalid, expired, user not found/inactive, or no active sessions
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

    # Check if user has at least one active session
    active_session = await fetch_one(
        """
        SELECT id FROM user_sessions
        WHERE user_id = $1 AND is_active = TRUE AND expires_at > NOW()
        LIMIT 1
        """,
        user_id
    )

    if not active_session:
        logger.warning(f"No active session for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert UUID to string for Pydantic validation
    return CurrentUser(
        id=str(user["id"]),
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        role_id=user["role_id"],
        is_active=user["is_active"]
    )


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


# ============================================================================
# API KEY AUTHENTICATION
# ============================================================================


async def require_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> dict:
    """
    Require valid API key for route access.

    Usage:
        @router.get("/api/inventory")
        async def get_inventory(user_info: dict = Depends(require_api_key)):
            # user_info contains: api_key_id, user_id, email, role_name, scopes

    Args:
        request: FastAPI request object
        x_api_key: API key from X-API-Key header

    Returns:
        Dictionary with user info and API key details

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
        )

    # Verify API key
    db = get_db()
    user_info = await api_key_service.verify_api_key(db, x_api_key)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )

    # Log usage (non-blocking - errors are logged but don't fail the request)
    try:
        await api_key_service.log_api_key_usage(
            db,
            api_key_id=user_info['api_key_id'],
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )
    except Exception as e:
        logger.warning(f"Failed to log API key usage: {e}")

    return user_info


def require_api_key_scope(required_scope: str):
    """
    Factory for scope-based API key authentication.

    Usage:
        @router.post("/api/inventory")
        async def create_item(user_info: dict = Depends(require_api_key_scope("inventory:write"))):
            # Only API keys with inventory:write scope can access

    Args:
        required_scope: Required scope (e.g., "inventory:read", "tickets:write")

    Returns:
        Dependency function that checks API key and scope
    """
    async def dependency(
        user_info: dict = Depends(require_api_key)
    ) -> dict:
        """Check if API key has required scope"""
        if not await api_key_service.check_scope(user_info['scopes'], required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}",
            )
        return user_info

    return dependency


async def get_current_user_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> dict:
    """
    Allow both JWT and API key authentication.
    Tries API key first, falls back to JWT.

    Usage:
        @router.get("/api/data")
        async def get_data(user: dict = Depends(get_current_user_or_api_key)):
            # Works with both JWT tokens and API keys

    Args:
        request: FastAPI request object
        credentials: Optional JWT Bearer credentials
        x_api_key: Optional API key from header

    Returns:
        Dictionary with user info (format varies by auth method)

    Raises:
        HTTPException: If neither authentication method is valid
    """
    # Try API key first
    if x_api_key:
        db = get_db()
        user_info = await api_key_service.verify_api_key(db, x_api_key)
        if user_info:
            # Log usage
            try:
                await api_key_service.log_api_key_usage(
                    db,
                    api_key_id=user_info['api_key_id'],
                    endpoint=str(request.url.path),
                    method=request.method,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get('user-agent')
                )
            except Exception as e:
                logger.warning(f"Failed to log API key usage: {e}")

            return {
                'user_id': user_info['user_id'],
                'email': user_info['email'],
                'role': user_info['role_name'],
                'auth_method': 'api_key',
                'api_key_id': user_info['api_key_id']
            }

    # Fall back to JWT
    if credentials:
        try:
            current_user = await get_current_user(credentials.credentials)
            return {
                'user_id': current_user.id,
                'email': current_user.email,
                'role': current_user.role,
                'auth_method': 'jwt'
            }
        except HTTPException:
            pass

    # Neither authentication method worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either JWT token or API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )

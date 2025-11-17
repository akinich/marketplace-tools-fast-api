"""
================================================================================
Farm Management System - JWT Token Management
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial JWT token creation and verification
  - Access token and refresh token generation
  - Token decoding with expiry validation
  - User info extraction from tokens

================================================================================
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TOKEN TYPES
# ============================================================================

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


# ============================================================================
# TOKEN CREATION
# ============================================================================


def create_access_token(
    user_id: str,
    email: str,
    full_name: str,
    role: str,
    extra_data: Optional[Dict] = None,
) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User UUID
        email: User email
        full_name: User full name
        role: User role (Admin/User)
        extra_data: Optional additional claims

    Returns:
        Encoded JWT access token
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "full_name": full_name,
        "role": role,
        "type": TOKEN_TYPE_ACCESS,
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow(),  # Issued at
    }

    # Add extra data if provided
    if extra_data:
        payload.update(extra_data)

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token.

    Args:
        user_id: User UUID

    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "type": TOKEN_TYPE_REFRESH,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


# ============================================================================
# TOKEN VERIFICATION
# ============================================================================


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict, or None if invalid

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise


def verify_access_token(token: str) -> Optional[Dict]:
    """
    Verify access token and extract payload.

    Args:
        token: JWT access token

    Returns:
        Payload dict if valid, None otherwise
    """
    try:
        payload = decode_token(token)

        # Verify token type
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            logger.warning("Invalid token type - expected access token")
            return None

        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[Dict]:
    """
    Verify refresh token and extract payload.

    Args:
        token: JWT refresh token

    Returns:
        Payload dict if valid, None otherwise
    """
    try:
        payload = decode_token(token)

        # Verify token type
        if payload.get("type") != TOKEN_TYPE_REFRESH:
            logger.warning("Invalid token type - expected refresh token")
            return None

        return payload
    except JWTError:
        return None


# ============================================================================
# TOKEN EXTRACTION
# ============================================================================


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from token.

    Args:
        token: JWT token

    Returns:
        User ID (UUID string) or None
    """
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None


def get_user_role_from_token(token: str) -> Optional[str]:
    """
    Extract user role from access token.

    Args:
        token: JWT access token

    Returns:
        User role string or None
    """
    try:
        payload = verify_access_token(token)
        return payload.get("role") if payload else None
    except JWTError:
        return None


# ============================================================================
# TOKEN VALIDATION HELPERS
# ============================================================================


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired.

    Args:
        token: JWT token

    Returns:
        True if expired, False otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},  # Don't raise error on expiry
        )

        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return True

        return datetime.utcnow().timestamp() > exp_timestamp
    except JWTError:
        return True


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get token expiry datetime.

    Args:
        token: JWT token

    Returns:
        Expiry datetime or None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )

        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)

        return None
    except JWTError:
        return None

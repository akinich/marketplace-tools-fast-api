"""
API Key Service
File: backend/app/services/api_key_service.py
Description: Service for API key generation, verification, and management
"""
import secrets
import bcrypt
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from asyncpg import Connection

logger = logging.getLogger(__name__)

# Available scopes for API keys
# Format: resource:action
AVAILABLE_SCOPES = [
    # Inventory
    "inventory:read",
    "inventory:write",
    "inventory:delete",
    "inventory:*",

    # Tickets
    "tickets:read",
    "tickets:write",
    "tickets:delete",
    "tickets:*",

    # Users (Admin)
    "users:read",
    "users:write",
    "users:delete",
    "users:*",

    # Dashboard
    "dashboard:read",

    # Development
    "development:read",
    "development:write",
    "development:*",

    # Docs
    "docs:read",

    # Settings (Admin)
    "settings:read",
    "settings:write",
    "settings:*",

    # Webhooks (Admin)
    "webhooks:read",
    "webhooks:write",
    "webhooks:*",

    # Audit Logs (Admin)
    "audit:read",

    # Admin (Meta - includes all admin scopes)
    "admin:*",

    # God mode (use with caution - full access)
    "*:*"
]

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate API key with secure random bytes

    Returns:
        tuple: (full_key, key_hash, key_prefix)
            - full_key: The complete API key to be shown to user (only once)
            - key_hash: Bcrypt hash for database storage
            - key_prefix: First 12 characters for display purposes
    """
    # Generate random key with farm_ prefix
    random_bytes = secrets.token_urlsafe(32)
    key = f"farm_{random_bytes}"

    # Hash for storage (bcrypt with auto-generated salt)
    key_hash = bcrypt.hashpw(key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Prefix for display (first 12 chars, no ellipsis - that's added in UI)
    key_prefix = key[:12]

    return key, key_hash, key_prefix

async def create_api_key(
    conn: Connection,
    user_id: str,
    name: str,
    scopes: List[str],
    description: Optional[str] = None,
    expires_in_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new API key

    Args:
        conn: Database connection
        user_id: User ID who owns the key
        name: User-friendly name for the key
        scopes: List of permission scopes
        description: Optional description
        expires_in_days: Optional expiration in days (1-365)

    Returns:
        Dictionary with API key data including the full key (only time it's visible)

    Raises:
        ValueError: If scopes are invalid
    """
    # Validate scopes
    invalid_scopes = [s for s in scopes if s not in AVAILABLE_SCOPES]
    if invalid_scopes:
        raise ValueError(f"Invalid scopes: {', '.join(invalid_scopes)}")

    # Generate key
    api_key, key_hash, key_prefix = generate_api_key()

    # Calculate expiry
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # Insert into database
    created = await conn.fetchrow(
        """
        INSERT INTO api_keys (
            user_id, key_hash, key_prefix, name, description, scopes, expires_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, user_id, key_prefix, name, description, scopes, is_active, expires_at, created_at, last_used_at
        """,
        user_id,
        key_hash,
        key_prefix,
        name,
        description,
        scopes,
        expires_at
    )

    logger.info(f"Created API key '{name}' for user {user_id} with {len(scopes)} scopes")

    # Convert UUID to string for Pydantic validation
    result = dict(created)
    result['user_id'] = str(result['user_id'])

    return {
        **result,
        'api_key': api_key  # Return full key (only time it's shown)
    }

async def verify_api_key(
    conn: Connection,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    Verify API key and return user info

    Args:
        conn: Database connection
        api_key: The API key to verify

    Returns:
        Dictionary with user info and scopes if valid, None if invalid
    """
    # Get all active API keys
    api_keys = await conn.fetch(
        """
        SELECT
            ak.id, ak.user_id, ak.key_hash, ak.scopes, ak.is_active, ak.expires_at,
            au.email, up.role_id, r.role_name
        FROM api_keys ak
        JOIN user_profiles up ON ak.user_id = up.id
        JOIN auth.users au ON ak.user_id = au.id
        JOIN roles r ON up.role_id = r.id
        WHERE ak.is_active = true
          AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
        """
    )

    # Check each key (bcrypt comparison)
    for key_row in api_keys:
        try:
            if bcrypt.checkpw(api_key.encode('utf-8'), key_row['key_hash'].encode('utf-8')):
                # Update last used timestamp
                await conn.execute(
                    "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
                    key_row['id']
                )

                logger.debug(f"API key verified for user {key_row['email']}")

                return {
                    'api_key_id': key_row['id'],
                    'user_id': key_row['user_id'],
                    'email': key_row['email'],
                    'role_id': key_row['role_id'],
                    'role_name': key_row['role_name'],
                    'scopes': key_row['scopes']
                }
        except Exception as e:
            logger.error(f"Error checking API key: {e}")
            continue

    logger.warning("Invalid API key attempted")
    return None

async def check_scope(scopes: List[str], required_scope: str) -> bool:
    """
    Check if API key has required scope

    Args:
        scopes: List of scopes the API key has
        required_scope: The scope required for the operation (e.g., "inventory:read")

    Returns:
        True if API key has the required scope, False otherwise
    """
    # God mode - full access
    if "*:*" in scopes:
        return True

    # Admin wildcard - access to admin resources
    if "admin:*" in scopes and required_scope.split(':')[0] in [
        'users', 'modules', 'settings', 'webhooks', 'audit'
    ]:
        return True

    # Exact match
    if required_scope in scopes:
        return True

    # Wildcard match (e.g., "inventory:*" includes "inventory:read")
    resource = required_scope.split(':')[0]
    if f"{resource}:*" in scopes:
        return True

    return False

async def log_api_key_usage(
    conn: Connection,
    api_key_id: int,
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    response_time_ms: Optional[int] = None
):
    """
    Log API key usage

    Args:
        conn: Database connection
        api_key_id: ID of the API key used
        endpoint: API endpoint accessed
        method: HTTP method
        status_code: HTTP response status code
        ip_address: Client IP address
        user_agent: Client user agent
        response_time_ms: Response time in milliseconds
    """
    try:
        await conn.execute(
            """
            INSERT INTO api_key_usage (
                api_key_id, endpoint, method, status_code, ip_address, user_agent, response_time_ms
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            api_key_id,
            endpoint,
            method,
            status_code,
            ip_address,
            user_agent,
            response_time_ms
        )
    except Exception as e:
        logger.error(f"Failed to log API key usage: {e}")

async def revoke_api_key(conn: Connection, api_key_id: int, user_id: str) -> bool:
    """
    Revoke an API key

    Args:
        conn: Database connection
        api_key_id: ID of the API key to revoke
        user_id: User ID (for ownership verification)

    Returns:
        True if key was revoked, False if not found or user doesn't own it
    """
    result = await conn.execute(
        """
        UPDATE api_keys
        SET is_active = false, revoked_at = NOW()
        WHERE id = $1 AND user_id = $2
        """,
        api_key_id,
        user_id
    )

    success = result != "UPDATE 0"
    if success:
        logger.info(f"Revoked API key {api_key_id} for user {user_id}")

    return success

async def get_user_api_keys(conn: Connection, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all API keys for a user

    Args:
        conn: Database connection
        user_id: User ID

    Returns:
        List of API key dictionaries
    """
    keys = await conn.fetch(
        """
        SELECT id, user_id, key_prefix, name, description, scopes, is_active,
               expires_at, last_used_at, created_at, revoked_at
        FROM api_keys
        WHERE user_id = $1
        ORDER BY created_at DESC
        """,
        user_id
    )
    # Convert UUID to string for Pydantic validation
    return [{**dict(k), 'user_id': str(k['user_id'])} for k in keys]

async def get_api_key_usage(
    conn: Connection,
    api_key_id: int,
    user_id: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get usage logs for an API key

    Args:
        conn: Database connection
        api_key_id: ID of the API key
        user_id: User ID (for ownership verification)
        limit: Maximum number of records to return

    Returns:
        List of usage log dictionaries
    """
    # Verify ownership
    key = await conn.fetchrow(
        "SELECT user_id FROM api_keys WHERE id = $1",
        api_key_id
    )

    if not key or key['user_id'] != user_id:
        return []

    usage = await conn.fetch(
        """
        SELECT id, endpoint, method, status_code, ip_address, created_at
        FROM api_key_usage
        WHERE api_key_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        api_key_id,
        limit
    )

    return [dict(u) for u in usage]

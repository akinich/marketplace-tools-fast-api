"""
================================================================================
Settings Helper - Database-first settings with env fallback
================================================================================
Version: 1.0.0
Last Updated: 2025-11-23

Description:
  Provides helper functions to fetch settings from the database first,
  with automatic fallback to environment variables if database is unavailable
  or setting doesn't exist. Includes comprehensive logging and debugging.

Usage:
  # Async context (with database connection)
  value = await get_setting_with_fallback(conn, "TELEGRAM_BOT_TOKEN", env_fallback=settings.TELEGRAM_BOT_TOKEN)

  # Sync context (no database available)
  value = get_setting_from_env("TELEGRAM_BOT_TOKEN")

================================================================================
"""

import logging
from typing import Any, Optional
from asyncpg import Connection
import os

from app.config import settings
from app.services import settings_service

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE-FIRST SETTINGS RETRIEVAL
# ============================================================================


async def get_setting_with_fallback(
    conn: Optional[Connection],
    setting_key: str,
    env_fallback: Any = None,
    default: Any = None,
    use_cache: bool = True
) -> Any:
    """
    Get a setting value with database-first approach and env fallback.

    Priority:
    1. Try to fetch from database (system_settings table)
    2. If database unavailable or setting not found, use env_fallback
    3. If env_fallback is None, use default

    Args:
        conn: Database connection (optional, if None will skip database lookup)
        setting_key: The setting key to fetch
        env_fallback: Value from environment variable to use as fallback
        default: Default value if all else fails
        use_cache: Whether to use settings cache (default: True)

    Returns:
        Setting value from database, env, or default

    Example:
        # Get Telegram bot token with fallback to env
        bot_token = await get_setting_with_fallback(
            conn,
            "telegram_bot_token",
            env_fallback=settings.TELEGRAM_BOT_TOKEN,
            default=""
        )
    """

    # Step 1: Try database if connection is provided
    if conn is not None:
        try:
            logger.debug(f"Attempting to fetch '{setting_key}' from database...")
            db_value = await settings_service.get_setting(
                conn,
                setting_key,
                default=None,
                use_cache=use_cache
            )

            if db_value is not None:
                logger.info(
                    f"✅ Setting '{setting_key}' loaded from database "
                    f"(value length: {len(str(db_value)) if db_value else 0} chars)"
                )
                return db_value
            else:
                logger.debug(f"Setting '{setting_key}' not found in database, trying fallback...")

        except Exception as e:
            logger.warning(
                f"⚠️ Failed to fetch '{setting_key}' from database: {e}. "
                f"Falling back to environment variable."
            )
    else:
        logger.debug(f"No database connection provided for '{setting_key}', using fallback...")

    # Step 2: Try environment variable fallback
    if env_fallback is not None:
        logger.info(
            f"📁 Setting '{setting_key}' loaded from environment variable "
            f"(value length: {len(str(env_fallback)) if env_fallback else 0} chars)"
        )
        return env_fallback

    # Step 3: Use default value
    logger.warning(
        f"⚠️ Setting '{setting_key}' not found in database or environment. "
        f"Using default value: {default}"
    )
    return default


def get_setting_from_env(setting_key: str, default: Any = None) -> Any:
    """
    Get a setting directly from environment variables (sync version).

    Use this when:
    - You don't have access to a database connection
    - You're in a synchronous context
    - You need a quick fallback without database lookup

    Args:
        setting_key: The setting key (will be converted to uppercase)
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    env_key = setting_key.upper()
    value = os.getenv(env_key, default)

    if value is not None and value != default:
        logger.debug(f"Setting '{env_key}' loaded from environment")
    else:
        logger.debug(f"Setting '{env_key}' not in environment, using default")

    return value


# ============================================================================
# SPECIALIZED GETTERS FOR COMMON SETTINGS
# ============================================================================


async def get_telegram_bot_token(conn: Optional[Connection] = None) -> Optional[str]:
    """
    Get Telegram bot token with database-first approach.

    Priority:
    1. Database: system_settings.telegram_bot_token
    2. Environment: TELEGRAM_BOT_TOKEN
    3. Default: None

    Args:
        conn: Database connection (optional)

    Returns:
        Telegram bot token or None
    """
    token = await get_setting_with_fallback(
        conn,
        "telegram_bot_token",
        env_fallback=settings.TELEGRAM_BOT_TOKEN,
        default=None
    )

    if not token:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN not configured in database or environment")
        return None

    return token


async def get_supabase_credentials(
    conn: Optional[Connection] = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Get Supabase URL and Service Key with database-first approach.

    Priority:
    1. Database: system_settings.supabase_url and supabase_service_key
    2. Environment: SUPABASE_URL and SUPABASE_SERVICE_KEY
    3. Default: (None, None)

    Args:
        conn: Database connection (optional)

    Returns:
        Tuple of (supabase_url, supabase_service_key)
    """
    supabase_url = await get_setting_with_fallback(
        conn,
        "supabase_url",
        env_fallback=settings.SUPABASE_URL,
        default=None
    )

    supabase_service_key = await get_setting_with_fallback(
        conn,
        "supabase_service_key",
        env_fallback=settings.SUPABASE_SERVICE_KEY,
        default=None
    )

    if not supabase_url or not supabase_service_key:
        logger.warning(
            "⚠️ Supabase credentials incomplete. "
            f"URL: {'✓' if supabase_url else '✗'}, "
            f"Service Key: {'✓' if supabase_service_key else '✗'}"
        )

    return supabase_url, supabase_service_key


# ============================================================================
# DIAGNOSTIC FUNCTIONS
# ============================================================================


async def diagnose_setting(
    conn: Optional[Connection],
    setting_key: str,
    env_key: Optional[str] = None
) -> dict:
    """
    Diagnose where a setting is coming from and its status.

    Useful for debugging configuration issues.

    Args:
        conn: Database connection
        setting_key: Database setting key
        env_key: Environment variable key (defaults to setting_key.upper())

    Returns:
        Dictionary with diagnostic information
    """
    if env_key is None:
        env_key = setting_key.upper()

    result = {
        "setting_key": setting_key,
        "env_key": env_key,
        "in_database": False,
        "in_environment": False,
        "value_source": None,
        "value_length": 0,
        "errors": []
    }

    # Check database
    if conn is not None:
        try:
            db_value = await settings_service.get_setting(conn, setting_key, default=None, use_cache=False)
            if db_value is not None:
                result["in_database"] = True
                result["value_source"] = "database"
                result["value_length"] = len(str(db_value))
        except Exception as e:
            result["errors"].append(f"Database error: {str(e)}")
    else:
        result["errors"].append("No database connection provided")

    # Check environment
    env_value = os.getenv(env_key)
    if env_value is not None:
        result["in_environment"] = True
        if result["value_source"] is None:
            result["value_source"] = "environment"
            result["value_length"] = len(str(env_value))

    # Overall status
    if not result["in_database"] and not result["in_environment"]:
        result["value_source"] = "missing"
        result["errors"].append("Setting not found in database or environment")

    return result

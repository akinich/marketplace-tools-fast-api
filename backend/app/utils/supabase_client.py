"""
================================================================================
Supabase Client Utility
================================================================================
Version: 2.0.0
Last Updated: 2025-11-23

Changelog:
----------
v2.0.0 (2025-11-23):
  - BREAKING: Changed to database-first configuration with env fallback
  - Added async get_supabase_client_async() for database lookup
  - Kept sync get_supabase_client() for backward compatibility (env only)
  - Added comprehensive logging and error handling
  - Added fallback mechanism if database unavailable

v1.0.1 (2025-11-18):
  - Fixed Client initialization to use correct API
  - Removed proxy parameter (not supported in supabase-py 2.3.0)

v1.0.0 (2025-11-17):
  - Initial implementation
================================================================================
"""

from supabase import create_client, Client
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Singleton Supabase client
_supabase_client: Client | None = None

# Import settings helper for database-first configuration
try:
    from app.utils.settings_helper import get_supabase_credentials
    from app.database import get_db
    _has_settings_helper = True
except ImportError:
    logger.warning("Settings helper not available, using direct env access for Supabase")
    _has_settings_helper = False


async def get_supabase_client_async() -> Client:
    """
    Get or create Supabase client singleton with database-first configuration.

    Priority:
    1. Database: system_settings.supabase_url and supabase_service_key
    2. Environment: SUPABASE_URL and SUPABASE_SERVICE_KEY
    3. Error if neither available

    Returns:
        Supabase Client instance

    Raises:
        RuntimeError: If Supabase credentials are not configured
    """
    global _supabase_client

    if _supabase_client is None:
        supabase_url = None
        supabase_service_key = None

        # Try database-first approach if helper available
        if _has_settings_helper:
            try:
                pool = get_db()
                async with pool.acquire() as conn:
                    supabase_url, supabase_service_key = await get_supabase_credentials(conn)
                    logger.debug("Attempted to fetch Supabase credentials from database")
            except Exception as e:
                logger.warning(
                    f"⚠️ Database unavailable for Supabase credentials lookup: {e}. "
                    f"Falling back to environment variables."
                )

        # Fallback to environment variables if database didn't provide values
        if not supabase_url or not supabase_service_key:
            logger.debug("Using environment variables for Supabase credentials")
            supabase_url = settings.SUPABASE_URL if settings.SUPABASE_URL else None
            supabase_service_key = settings.SUPABASE_SERVICE_KEY if settings.SUPABASE_SERVICE_KEY else None

        # Validate we have credentials
        if not supabase_url or not supabase_service_key:
            error_msg = (
                "❌ Supabase credentials not configured. "
                "Please configure via Settings UI or environment variables. "
                f"URL: {'✗ missing' if not supabase_url else '✓'}, "
                f"Service Key: {'✗ missing' if not supabase_service_key else '✓'}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Create client
        try:
            _supabase_client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_service_key
            )
            logger.info(
                f"✅ Supabase client initialized successfully "
                f"(URL: {supabase_url[:30]}...)"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise

    return _supabase_client


def get_supabase_client() -> Client:
    """
    Get or create Supabase client singleton (synchronous version).

    DEPRECATED: Use get_supabase_client_async() in async contexts for database-first approach.
    This function only checks environment variables.

    Returns:
        Supabase Client instance

    Raises:
        RuntimeError: If Supabase credentials are not configured in environment
    """
    global _supabase_client

    if _supabase_client is None:
        supabase_url = settings.SUPABASE_URL if settings.SUPABASE_URL else None
        supabase_service_key = settings.SUPABASE_SERVICE_KEY if settings.SUPABASE_SERVICE_KEY else None

        if not supabase_url or not supabase_service_key:
            error_msg = (
                "❌ Supabase credentials not configured in environment. "
                f"URL: {'✗ missing' if not supabase_url else '✓'}, "
                f"Service Key: {'✗ missing' if not supabase_service_key else '✓'}. "
                "Use get_supabase_client_async() for database-first approach."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            _supabase_client = create_client(
                supabase_url=supabase_url,
                supabase_key=supabase_service_key
            )
            logger.info("✅ Supabase client initialized from environment variables")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise

    return _supabase_client

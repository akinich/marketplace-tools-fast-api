"""
================================================================================
Supabase Client Utility
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Provides Supabase client for password reset emails and other Supabase Auth operations.
================================================================================
"""

from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Singleton Supabase client
_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client singleton.

    Returns:
        Supabase Client instance
    """
    global _supabase_client

    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise

    return _supabase_client

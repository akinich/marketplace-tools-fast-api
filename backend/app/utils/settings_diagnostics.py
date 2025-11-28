"""
================================================================================
Settings Diagnostics - Startup configuration verification
================================================================================
Logs which settings are loaded from database vs environment variables
Runs at application startup to provide visibility into configuration sources
================================================================================
"""

import logging
from typing import Optional
from asyncpg import Connection

from app.database import fetch_one, pool

logger = logging.getLogger(__name__)


async def diagnose_settings_at_startup():
    """
    Run at startup to diagnose and log where critical settings are coming from.
    Logs at INFO level so it's visible in production logs.
    """

    logger.info("=" * 80)
    logger.info("⚙️  SETTINGS DIAGNOSTICS - Checking configuration sources")
    logger.info("=" * 80)

    critical_settings = [
        ('telegram_bot_token', 'Telegram Bot'),
        ('supabase_url', 'Supabase URL'),
        ('supabase_service_key', 'Supabase Service Key')
    ]

    try:
        async with pool.acquire() as conn:
            logger.info("🔍 Checking database settings...")

            for setting_key, display_name in critical_settings:
                result = await fetch_one(
                    "SELECT setting_key, setting_value, category FROM system_settings WHERE setting_key = $1",
                    setting_key
                )

                if result:
                    value_preview = str(result['setting_value'])[:20] + "..." if len(str(result['setting_value'])) > 20 else str(result['setting_value'])
                    logger.info(
                        f"  ✅ {display_name:<25} → DATABASE (category: {result['category']}, "
                        f"value: {value_preview})"
                    )
                else:
                    logger.warning(
                        f"  ⚠️  {display_name:<25} → NOT IN DATABASE (will use environment variable)"
                    )

            # Count total settings
            total_count = await fetch_one(
                "SELECT COUNT(*) as count FROM system_settings"
            )
            logger.info(f"📊 Total settings in database: {total_count['count'] if total_count else 0}")

    except Exception as e:
        logger.error(f"❌ Failed to check database settings: {e}")
        logger.info("   → Application will use environment variables as fallback")

    logger.info("=" * 80)

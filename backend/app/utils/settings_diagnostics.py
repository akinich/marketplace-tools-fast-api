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
    logger.info("⚙️  SETTINGS DIAGNOSTICS - Database Configuration Status")
    logger.info("=" * 80)

    try:
        async with pool.acquire() as conn:
            # Get all settings grouped by category
            all_settings = await conn.fetch("""
                SELECT category, setting_key, setting_value, is_public, is_encrypted
                FROM system_settings
                ORDER BY category, setting_key
            """)

            if not all_settings:
                logger.warning("⚠️  No settings found in database!")
                logger.info("   → All configuration will use environment variables")
            else:
                # Group by category
                categories = {}
                for row in all_settings:
                    cat = row['category']
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(row)

                # Log summary by category
                logger.info(f"📊 Found {len(all_settings)} settings across {len(categories)} categories")
                logger.info("")

                for category, settings in sorted(categories.items()):
                    logger.info(f"📁 Category: {category.upper()}")
                    for setting in settings:
                        key = setting['setting_key']
                        value = setting['setting_value']

                        # Mask sensitive values
                        if setting['is_encrypted'] or 'password' in key or 'secret' in key or 'key' in key or 'token' in key:
                            display_value = "***MASKED***"
                        elif len(str(value)) > 30:
                            display_value = str(value)[:30] + "..."
                        else:
                            display_value = str(value)

                        visibility = "🔒 Private" if not setting['is_public'] else "🌐 Public"
                        logger.info(f"   • {key:<35} = {display_value:<35} {visibility}")
                    logger.info("")

                # Highlight critical integrations
                logger.info("🔑 Critical Integration Settings:")
                critical_keys = ['telegram_bot_token', 'supabase_url', 'supabase_service_key']
                for key in critical_keys:
                    found = any(s['setting_key'] == key for s in all_settings)
                    status = "✅ Configured in DB" if found else "❌ Missing (using env)"
                    logger.info(f"   • {key:<30} {status}")

    except Exception as e:
        logger.error(f"❌ Failed to check database settings: {e}")
        logger.info("   → Application will use environment variables as fallback")

    logger.info("=" * 80)

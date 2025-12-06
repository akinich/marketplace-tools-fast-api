"""
================================================================================
Marketplace ERP - Background Task Scheduler
================================================================================
Version: 2.2.0
Last Updated: 2025-12-02

Purpose:
--------
APScheduler-based background task management for recurring operations.

Tasks:
------
1. Sync Zoho Items from Zoho Books (daily at 4:00 AM IST)
2. Sync Woo Items from WooCommerce (daily at 4:00 AM IST)
3. Process webhook delivery queue (every 1 minute)
4. Process email queue (every 5 minutes)

Changelog:
----------
v2.2.0 (2025-12-02):
  - Added Zoho Items sync scheduled task
  - Added Woo Items sync scheduled task
  - Both run daily at 4:00 AM IST
  - Zoho: Only syncs items modified in last 24 hours (not force refresh)
  - Woo: Syncs up to 1000 items with update_existing=True
  - Uses system user ID for automated syncs

v2.1.0 (2025-11-22):
  - Added webhook delivery queue processing task
  - Runs every 2 minutes to send pending webhooks
  - Added email queue processing task
  - Runs every 5 minutes to send pending emails

v2.0.0 (2025-11-20):
  - Initial version with notification tasks

================================================================================
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from app.database import fetch_one, fetch_all, execute_query, get_db
from app.services import telegram_service, webhook_service, email_service, zoho_item_service, product_service
from app.services import zoho_vendor_service, zoho_customer_service, woo_customer_service, wastage_tracking_service
from app.schemas.product import WooCommerceSyncRequest

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


async def sync_zoho_items_daily():
    """
    Sync items from Zoho Books daily at 4:00 AM IST.
    This is a scheduled task that runs automatically.
    """
    try:
        logger.info("🔄 Starting scheduled Zoho Items sync...")

        # Use system user ID for scheduled syncs
        system_user_id = "00000000-0000-0000-0000-000000000000"

        result = await zoho_item_service.sync_from_zoho_books(
            synced_by=system_user_id,
            force_refresh=False  # Only sync items modified in last 24 hours
        )

        logger.info(
            f"✅ Scheduled Zoho sync completed: "
            f"{result['added']} added, {result['updated']} updated, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )

    except Exception as e:
        logger.error(f"❌ Error in scheduled Zoho sync: {e}", exc_info=True)


async def sync_woo_items_daily():
    """
    Sync items from WooCommerce daily at 4:00 AM IST.
    This is a scheduled task that runs automatically.
    """
    try:
        logger.info("🔄 Starting scheduled WooCommerce sync...")

        # Use system user ID for scheduled syncs
        system_user_id = "00000000-0000-0000-0000-000000000000"

        sync_request = WooCommerceSyncRequest(limit=1000, update_existing=True)
        result = await product_service.sync_from_woocommerce(
            sync_request=sync_request,
            synced_by=system_user_id
        )

        logger.info(
            f"✅ Scheduled WooCommerce sync completed: "
            f"{result['added']} added, {result['updated']} updated, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )

    except Exception as e:
        logger.error(f"❌ Error in scheduled WooCommerce sync: {e}", exc_info=True)


async def sync_zoho_vendors_daily():
    """
    Sync vendors from Zoho Books daily at 4:00 AM IST.
    This is a scheduled task that runs automatically.
    """
    try:
        logger.info("🔄 Starting scheduled Zoho Vendors sync...")

        # Use system user ID for scheduled syncs
        system_user_id = "00000000-0000-0000-0000-000000000000"

        result = await zoho_vendor_service.sync_from_zoho_books(
            synced_by=system_user_id,
            force_refresh=False  # Only sync vendors modified in last 24 hours
        )

        logger.info(
            f"✅ Scheduled Zoho Vendors sync completed: "
            f"{result['added']} added, {result['updated']} updated, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )

    except Exception as e:
        logger.error(f"❌ Error in scheduled Zoho Vendors sync: {e}", exc_info=True)


async def sync_zoho_customers_daily():
    """
    Sync customers from Zoho Books daily at 4:00 AM IST.
    This is a scheduled task that runs automatically.
    """
    try:
        logger.info("🔄 Starting scheduled Zoho Customers sync...")

        # Use system user ID for scheduled syncs
        system_user_id = "00000000-0000-0000-0000-000000000000"

        result = await zoho_customer_service.sync_from_zoho_books(
            synced_by=system_user_id,
            force_refresh=False  # Only sync customers modified in last 24 hours
        )

        logger.info(
            f"✅ Scheduled Zoho Customers sync completed: "
            f"{result['added']} added, {result['updated']} updated, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )

    except Exception as e:
        logger.error(f"❌ Error in scheduled Zoho Customers sync: {e}", exc_info=True)


async def sync_woo_customers_daily():
    """
    Sync customers from WooCommerce daily at 4:00 AM IST.
    This is a scheduled task that runs automatically.
    """
    try:
        logger.info("🔄 Starting scheduled WooCommerce Customers sync...")

        # Use system user ID for scheduled syncs
        system_user_id = "00000000-0000-0000-0000-000000000000"

        result = await woo_customer_service.sync_from_woocommerce(
            synced_by=system_user_id
        )

        logger.info(
            f"✅ Scheduled WooCommerce Customers sync completed: "
            f"{result['added']} added, {result['updated']} updated, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )

    except Exception as e:
        logger.error(f"❌ Error in scheduled WooCommerce Customers sync: {e}", exc_info=True)




async def process_webhook_queue():
    """
    Process pending webhook deliveries.
    Runs every 2 minutes.
    """
    try:
        logger.debug("Processing webhook delivery queue...")

        pool = get_db()
        async with pool.acquire() as conn:
            await webhook_service.process_webhook_queue(conn, batch_size=20)

        logger.debug("Webhook queue processing completed")

    except Exception as e:
        logger.error(f"❌ Error processing webhook queue: {e}", exc_info=True)


async def process_email_queue():
    """
    Process pending emails in the queue.
    Runs every 5 minutes.
    """
    try:
        logger.debug("Processing email queue...")

        pool = get_db()
        async with pool.acquire() as conn:
            await email_service.process_email_queue(conn, batch_size=20)

        logger.debug("Email queue processing completed")

    except Exception as e:
        logger.error(f"❌ Error processing email queue: {e}", exc_info=True)


async def check_wastage_thresholds():
    """
    Check wastage thresholds and generate alerts.
    Runs every hour at the top of the hour.
    """
    try:
        logger.debug("Checking wastage thresholds...")

        result = await wastage_tracking_service.check_threshold_alerts()
        
        if result.alerts:
            logger.info(f"⚠️ Generated {len(result.alerts)} wastage alerts")
        else:
            logger.debug("No wastage threshold alerts")

    except Exception as e:
        logger.error(f"❌ Error checking wastage thresholds: {e}", exc_info=True)


def start_scheduler():
    """
    Start the background scheduler with all scheduled tasks.
    """
    global scheduler

    try:
        scheduler = AsyncIOScheduler()

        # Task 1: Sync Zoho Items daily at 4:00 AM IST
        scheduler.add_job(
            sync_zoho_items_daily,
            trigger=CronTrigger(hour=4, minute=0, timezone='Asia/Kolkata'),
            id="sync_zoho_items_daily",
            name="Sync Zoho Items from Zoho Books",
            replace_existing=True,
            max_instances=1,
        )

        # Task 2: Process webhook delivery queue every 1 minute
        scheduler.add_job(
            process_webhook_queue,
            trigger=IntervalTrigger(minutes=1),
            id="process_webhook_queue",
            name="Process webhook delivery queue",
            replace_existing=True,
            max_instances=1,
        )

        # Task 3: Process email queue every 5 minutes
        scheduler.add_job(
            process_email_queue,
            trigger=IntervalTrigger(minutes=5),
            id="process_email_queue",
            name="Process email queue",
            replace_existing=True,
            max_instances=1,
        )

        # Task 4: Sync Woo Items daily at 4:00 AM IST
        scheduler.add_job(
            sync_woo_items_daily,
            trigger=CronTrigger(hour=4, minute=0, timezone='Asia/Kolkata'),
            id="sync_woo_items_daily",
            name="Sync Woo Items from WooCommerce",
            replace_existing=True,
            max_instances=1,
        )

        # Task 5: Sync Zoho Vendors daily at 4:00 AM IST
        scheduler.add_job(
            sync_zoho_vendors_daily,
            trigger=CronTrigger(hour=4, minute=0, timezone='Asia/Kolkata'),
            id="sync_zoho_vendors_daily",
            name="Sync Zoho Vendors from Zoho Books",
            replace_existing=True,
            max_instances=1,
        )

        # Task 6: Sync Zoho Customers daily at 4:00 AM IST
        scheduler.add_job(
            sync_zoho_customers_daily,
            trigger=CronTrigger(hour=4, minute=0, timezone='Asia/Kolkata'),
            id="sync_zoho_customers_daily",
            name="Sync Zoho Customers from Zoho Books",
            replace_existing=True,
            max_instances=1,
        )

        # Task 7: Sync WooCommerce Customers daily at 4:00 AM IST
        scheduler.add_job(
            sync_woo_customers_daily,
            trigger=CronTrigger(hour=4, minute=0, timezone='Asia/Kolkata'),
            id="sync_woo_customers_daily",
            name="Sync WooCommerce Customers from WooCommerce",
            replace_existing=True,
            max_instances=1,
        )

        # Task 8: Check wastage thresholds hourly
        scheduler.add_job(
            check_wastage_thresholds,
            trigger=CronTrigger(minute=0, timezone='Asia/Kolkata'),  # Top of every hour
            id="check_wastage_thresholds",
            name="Check wastage thresholds and generate alerts",
            replace_existing=True,
            max_instances=1,
        )

        scheduler.start()
        logger.info("✅ Background scheduler started successfully")
        logger.info("📅 Scheduled tasks:")
        logger.info("   - Sync Zoho Items: Daily at 4:00 AM IST")
        logger.info("   - Sync Woo Items: Daily at 4:00 AM IST")
        logger.info("   - Sync Zoho Vendors: Daily at 4:00 AM IST")
        logger.info("   - Sync Zoho Customers: Daily at 4:00 AM IST")
        logger.info("   - Sync WooCommerce Customers: Daily at 4:00 AM IST")
        logger.info("   - Process webhook queue: Every 1 minute")
        logger.info("   - Process email queue: Every 5 minutes")
        logger.info("   - Check wastage thresholds: Every hour")

    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
        raise


def stop_scheduler():
    """
    Stop the background scheduler gracefully.
    """
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("✅ Background scheduler stopped")
    else:
        logger.debug("Scheduler was not running")


def get_scheduler_status():
    """
    Get current scheduler status and job information.
    """
    global scheduler

    if not scheduler:
        return {"status": "not_initialized", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
        )

    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs,
    }

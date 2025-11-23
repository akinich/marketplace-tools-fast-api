"""
================================================================================
Farm Management System - Background Task Scheduler
================================================================================
Version: 2.1.0
Last Updated: 2025-11-22

Purpose:
--------
APScheduler-based background task management for recurring operations.

Tasks:
------
1. Auto-expire old inventory reservations (every 15 minutes)
2. Low stock first alerts (every hour)
3. Low stock daily summary (daily at 9 AM)
4. Process webhook delivery queue (every 2 minutes)
5. Process email queue (every 5 minutes)

Changelog:
----------
v2.1.0 (2025-11-22):
  - Added webhook delivery queue processing task
  - Runs every 2 minutes to send pending webhooks
  - Added email queue processing task
  - Runs every 5 minutes to send pending emails

v2.0.0 (2025-11-20):
  - Initial version with inventory and notification tasks

================================================================================
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from app.database import fetch_one, fetch_all, execute_query, get_db
from app.services import telegram_service, webhook_service, email_service

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


async def expire_inventory_reservations():
    """
    Auto-expire pending reservations that are past their reserved_until time.
    Runs every 15 minutes.
    """
    try:
        # Log expired reservations before updating
        expired_reservations = await fetch_one(
            """
            SELECT COUNT(*) as count
            FROM inventory_reservations
            WHERE status = 'pending' AND reserved_until < NOW()
            """
        )

        count = expired_reservations.get("count", 0) if expired_reservations else 0

        if count > 0:
            logger.info(f"Expiring {count} old reservations...")

            # Call the database function to expire reservations
            result = await fetch_one("SELECT expire_old_reservations() as expired_count")
            expired_count = result.get("expired_count", 0) if result else 0

            logger.info(f"✅ Successfully expired {expired_count} reservations")
        else:
            logger.debug("No expired reservations to process")

    except Exception as e:
        logger.error(f"❌ Error expiring reservations: {e}", exc_info=True)


async def check_low_stock_first_alerts():
    """
    Check for items that have dropped below reorder threshold and send first alert.
    Runs every hour.
    """
    try:
        logger.debug("Checking for low stock items (first alerts)...")

        # Get items below reorder threshold that haven't been alerted yet
        low_stock_items = await fetch_all(
            """
            SELECT
                im.id,
                im.item_name,
                im.category,
                im.unit,
                im.current_qty,
                im.reorder_threshold,
                (im.reorder_threshold - im.current_qty) as deficit,
                s.supplier_name as default_supplier_name
            FROM item_master im
            LEFT JOIN suppliers s ON s.id = im.default_supplier_id
            WHERE im.is_active = TRUE
              AND im.current_qty <= im.reorder_threshold
              AND NOT EXISTS (
                  SELECT 1 FROM low_stock_notifications lsn
                  WHERE lsn.item_master_id = im.id
                    AND lsn.is_resolved = FALSE
                    AND lsn.notification_type = 'first_alert'
              )
            ORDER BY (im.reorder_threshold - im.current_qty) DESC
            """
        )

        if low_stock_items:
            logger.info(f"Found {len(low_stock_items)} new low stock items")

            # Send first alert for each item
            for item in low_stock_items:
                await telegram_service.notify_low_stock_first_alert(dict(item))

            logger.info(f"✅ Sent first alerts for {len(low_stock_items)} items")
        else:
            logger.debug("No new low stock items to alert")

    except Exception as e:
        logger.error(f"❌ Error checking low stock alerts: {e}", exc_info=True)


async def send_low_stock_daily_summary():
    """
    Send daily summary of all low stock items.
    Runs daily at 9 AM.
    """
    try:
        logger.info("Sending daily low stock summary...")

        # Send the summary (service handles checking if there are items)
        success = await telegram_service.notify_low_stock_daily_summary()

        if success:
            logger.info("✅ Daily low stock summary sent successfully")
        else:
            logger.info("No low stock items for daily summary")

    except Exception as e:
        logger.error(f"❌ Error sending daily low stock summary: {e}", exc_info=True)


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


def start_scheduler():
    """
    Start the background scheduler with all scheduled tasks.
    """
    global scheduler

    try:
        scheduler = AsyncIOScheduler()

        # Task 1: Expire old reservations every 15 minutes
        scheduler.add_job(
            expire_inventory_reservations,
            trigger=IntervalTrigger(minutes=15),
            id="expire_reservations",
            name="Expire old inventory reservations",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping runs
        )

        # Task 2: Check for low stock first alerts every hour
        scheduler.add_job(
            check_low_stock_first_alerts,
            trigger=IntervalTrigger(hours=1),
            id="low_stock_first_alerts",
            name="Check for low stock first alerts",
            replace_existing=True,
            max_instances=1,
        )

        # Task 3: Send daily low stock summary at 9 AM
        scheduler.add_job(
            send_low_stock_daily_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id="low_stock_daily_summary",
            name="Send daily low stock summary",
            replace_existing=True,
            max_instances=1,
        )

        # Task 4: Process webhook delivery queue every 2 minutes
        scheduler.add_job(
            process_webhook_queue,
            trigger=IntervalTrigger(minutes=2),
            id="process_webhook_queue",
            name="Process webhook delivery queue",
            replace_existing=True,
            max_instances=1,
        )

        # Task 5: Process email queue every 5 minutes
        scheduler.add_job(
            process_email_queue,
            trigger=IntervalTrigger(minutes=5),
            id="process_email_queue",
            name="Process email queue",
            replace_existing=True,
            max_instances=1,
        )

        scheduler.start()
        logger.info("✅ Background scheduler started successfully")
        logger.info("📅 Scheduled tasks:")
        logger.info("   - Expire reservations: Every 15 minutes")
        logger.info("   - Low stock first alerts: Every hour")
        logger.info("   - Low stock daily summary: Daily at 9:00 AM")
        logger.info("   - Process webhook queue: Every 2 minutes")
        logger.info("   - Process email queue: Every 5 minutes")

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

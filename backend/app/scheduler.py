"""
================================================================================
Farm Management System - Background Task Scheduler
================================================================================
Version: 1.0.0
Last Updated: 2025-11-18

Purpose:
--------
APScheduler-based background task management for recurring operations.

Tasks:
------
1. Auto-expire old inventory reservations (every 15 minutes)
2. (Future) Stock level alerts
3. (Future) Expiry notifications

================================================================================
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.database import fetch_one, execute_query

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

        scheduler.start()
        logger.info("✅ Background scheduler started successfully")
        logger.info("📅 Scheduled tasks:")
        logger.info("   - Expire reservations: Every 15 minutes")

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

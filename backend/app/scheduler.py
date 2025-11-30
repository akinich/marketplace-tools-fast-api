"""
================================================================================
Marketplace ERP - Background Task Scheduler
================================================================================
Version: 2.1.0
Last Updated: 2025-11-22

Purpose:
--------
APScheduler-based background task management for recurring operations.

Tasks:
------

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
  - Initial version with notification tasks

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



        # Task 4: Process webhook delivery queue every 1 minute
        scheduler.add_job(
            process_webhook_queue,
            trigger=IntervalTrigger(minutes=1),
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

        logger.info("   - Process webhook queue: Every 1 minute")
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

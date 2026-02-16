"""Weekly analysis scheduler.

Manages the automated weekly execution cycle:
- Runs every Monday at a configurable time
- Fetches data, generates report, sends notifications
- Can be triggered via APScheduler or external cron/GitHub Actions
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import async_session_factory
from app.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def run_weekly_analysis():
    """Execute the weekly analysis pipeline.

    This is the main scheduled job that runs every Monday.
    """
    logger.info("Starting scheduled weekly analysis...")
    start_time = datetime.now()

    try:
        async with async_session_factory() as db:
            generator = ReportGenerator(db)
            result = await generator.generate_weekly_report(
                send_chatwork=True,
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Weekly analysis completed in {elapsed:.1f}s: "
                f"report={result['report_id']}, "
                f"proposals={result['proposals_generated']}"
            )

            if result.get("chatwork"):
                chatwork = result["chatwork"]
                logger.info(
                    f"Chatwork: message_sent={chatwork.get('message_sent')}, "
                    f"tasks_created={chatwork.get('tasks_created')}"
                )

            return result

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Weekly analysis failed after {elapsed:.1f}s: {e}",
            exc_info=True,
        )
        raise


def setup_scheduler(
    day_of_week: str = "mon",
    hour: int = 7,
    minute: int = 0,
):
    """Configure the weekly scheduler.

    Args:
        day_of_week: Day to run ('mon', 'tue', etc.)
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
    """
    trigger = CronTrigger(
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        timezone="Asia/Tokyo",
    )

    scheduler.add_job(
        run_weekly_analysis,
        trigger=trigger,
        id="weekly_analysis",
        name="Weekly Google Ads Analysis",
        replace_existing=True,
        misfire_grace_time=3600,  # Allow 1 hour delay
    )

    logger.info(
        f"Scheduler configured: weekly analysis on {day_of_week} "
        f"at {hour:02d}:{minute:02d} JST"
    )


def start_scheduler():
    """Start the scheduler."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")


def get_next_run_time() -> str | None:
    """Get the next scheduled run time."""
    job = scheduler.get_job("weekly_analysis")
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None

"""Scheduler process to run periodic jobs (APScheduler).

Usage:
  python run_jobs.py

This will start an in-process scheduler that runs the jobs defined in
`app.services.job_service` on the configured intervals.

Adjust schedules below as needed.
"""
import logging
import signal
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

# Ensure project root is on PYTHONPATH when running as script
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.services.job_service import FAQJobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("run_jobs")


def main():
    logger.info("Starting jobs scheduler")

    executors = {"default": ThreadPoolExecutor(10)}
    sched = BlockingScheduler(executors=executors)

    # Monthly reload: day 1 at 03:00
    sched.add_job(
        FAQJobs.reload_faqs,
        trigger="cron",
        day="1",
        hour="3",
        minute="0",
        id="reload_faqs_monthly",
        replace_existing=True,
    )

    # Integrity check: every 30 minutes
    sched.add_job(
        FAQJobs.test_faq_integrity,
        trigger="interval",
        minutes=30,
        id="faq_integrity",
        replace_existing=True,
    )

    # Optional: run a quick pipeline smoke test at startup (commented by default)
    # sched.add_job(FAQJobs.test_pipeline_with_sample_messages, trigger="date")

    def _shutdown(signum, frame):
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        try:
            sched.shutdown(wait=False)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()

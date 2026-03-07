import logging

from apscheduler.schedulers.background import BackgroundScheduler

import app.db.repository as repository
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

def run_automated_cleanup(days_inactive: int = 30):
    db = SessionLocal()
    try:
        deleted_count = repository.cleanup_inactive_links(db, days_inactive=days_inactive)
        if deleted_count > 0:
            logger.warning(f"Automated Cleanup: {deleted_count} inactive links were soft-deleted.")
    except Exception as e:
        logger.error(f"Automated Cleanup failed: {e}")
    finally:
        db.close()

def run_automated_purge(days_since_deleted: int = 30):
    db = SessionLocal()
    try:
        count = repository.purge_soft_deleted_links(db, days_since_deleted=days_since_deleted)
        if count > 0:
            logger.warning(f"Automated Purge: {count} links permanently erased from disk.")
    except Exception as e:
        logger.error(f"Automated Purge failed: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        run_automated_cleanup,
        'interval',
        days=1,
        kwargs={"days_inactive": 30}
    )

    scheduler.add_job(
        run_automated_purge,
        'interval',
        days=7,
        kwargs={"days_since_deleted": 30}
    )

    scheduler.start()
    logger.info("Background scheduler started successfully!")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Background scheduler safely shut down.")

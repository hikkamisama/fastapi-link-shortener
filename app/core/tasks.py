import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler

import app.db.repository as repository
from app.db.redis_cache import redis_client
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

def background_record_click(short_code: str):
    db = SessionLocal()
    try:
        link = repository.get_link_by_code(db, short_code)
        if link and link.is_active:
            link.clicks += 1
            link.last_clicked_at = datetime.now(UTC)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to record background click for {short_code}: {e}")
    finally:
        db.close()

def run_cache_popular_links(limit: int = 100):
    db = SessionLocal()
    try:
        popular_links = repository.get_popular_links(db, limit=limit)
        pipe = redis_client.pipeline()

        count = 0
        for link in popular_links:

            code = link.alias or link.short_id

            pipe.setex(f"link:{code}", 86400, link.original_url)
            count += 1

        pipe.execute()
        logger.info(f"Cache Warming Complete: Top {count} links loaded into Redis.")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
    finally:
        db.close()

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

    scheduler.add_job(
        run_cache_popular_links,
        'interval',
        days=1,
        kwargs={"limit": 100}
    )

    scheduler.start()
    logger.info("Background scheduler started successfully!")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Background scheduler safely shut down.")

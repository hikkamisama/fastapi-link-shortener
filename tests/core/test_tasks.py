import logging
from unittest.mock import MagicMock, patch

import pytest

from app.core import tasks
from app.db import repository


@pytest.fixture
def run_safely(db_session):
    with patch.object(db_session, 'close', return_value=None):
        with patch("app.core.tasks.SessionLocal", return_value=db_session):
            yield db_session


def test_background_record_click(run_safely, db_session):
    link = repository.create_short_link(db_session, "https://click.com", "bg-click")
    assert link.clicks == 0
    tasks.background_record_click("bg-click")
    db_session.refresh(link)
    assert link.clicks == 1

def test_background_record_click_exception(run_safely, caplog):
    with patch("app.core.tasks.repository.get_link_by_code", side_effect=Exception("DB Down")):
        tasks.background_record_click("any-code")
        assert "Failed to record background click" in caplog.text

def test_run_automated_cleanup_wrapper(run_safely, caplog):
    with patch("app.core.tasks.repository.cleanup_inactive_links", return_value=5):
        tasks.run_automated_cleanup(days_inactive=30)
        assert "Automated Cleanup: 5 inactive links were soft-deleted" in caplog.text

def test_run_automated_cleanup_wrapper_exception(run_safely, caplog):
    with patch(
        "app.core.tasks.repository.cleanup_inactive_links",
        side_effect=Exception("DB Down")
    ):
        tasks.run_automated_cleanup()
        assert "Automated Cleanup failed:" in caplog.text

def test_run_automated_purge_wrapper(run_safely, caplog):
    with patch("app.core.tasks.repository.purge_soft_deleted_links", return_value=12):
        tasks.run_automated_purge(days_since_deleted=30)
        assert "Automated Purge: 12 links" in caplog.text

def test_run_automated_purge_wrapper_exception(run_safely, caplog):
    with patch(
        "app.core.tasks.repository.purge_soft_deleted_links",
        side_effect=Exception("DB Down")
    ):
        tasks.run_automated_purge()
        assert "Automated Purge failed:" in caplog.text

def test_run_cache_popular_links(run_safely, caplog):
    caplog.set_level(logging.INFO)
    with patch("app.core.tasks.repository.get_popular_links", return_value=[]), \
         patch("app.core.tasks.redis_client.pipeline") as mock_pipeline:
        tasks.run_cache_popular_links(limit=10)
        mock_pipeline.return_value.execute.assert_called_once()
        assert "Cache Warming Complete" in caplog.text

def test_run_cache_popular_links_exception(run_safely, caplog):
    with patch("app.core.tasks.repository.get_popular_links", side_effect=Exception("Redis Down")):
        tasks.run_cache_popular_links()
        assert "Failed to warm cache" in caplog.text


def test_scheduler_startup_and_shutdown():
    with patch("app.core.tasks.scheduler") as mock_sched:
        tasks.start_scheduler()
        assert mock_sched.add_job.call_count == 3
        mock_sched.start.assert_called_once()
        tasks.stop_scheduler()
        mock_sched.shutdown.assert_called_once()



def test_run_cache_popular_links_with_data(run_safely, caplog):
    caplog.set_level(logging.INFO)
    fake_link = MagicMock()
    fake_link.alias = "pop-link"
    fake_link.original_url = "https://popular.com"
    with patch("app.core.tasks.repository.get_popular_links", return_value=[fake_link]), \
         patch("app.core.tasks.redis_client.pipeline") as mock_pipeline:
        tasks.run_cache_popular_links(limit=10)
        pipe_instance = mock_pipeline.return_value
        pipe_instance.setex.assert_called_once_with("link:pop-link", 86400, "https://popular.com")
        pipe_instance.execute.assert_called_once()
        assert "Cache Warming Complete" in caplog.text

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

import app.db.repository as repository


def test_create_short_link_random(db_session):
    link = repository.create_short_link(db_session, "https://example.com", "random123")
    assert link.original_url == "https://example.com"
    assert link.short_id == "random123"
    assert link.alias is None

def test_create_short_link_alias(db_session):
    link = repository.create_short_link(
        db_session, "https://example.com", "my-alias", alias="my-alias"
    )
    assert link.short_id == "my-alias"
    assert link.alias == "my-alias"

def test_soft_delete_mechanisms(db_session):
    link = repository.create_short_link(db_session, "https://example.com", "xyz456")

    assert link.is_active is True

    repository.soft_delete_link(db_session, link, reason="testing_delete")

    assert link.is_active is False
    assert link.deletion_reason == "testing_delete"
    assert link.deleted_at is not None

def test_hard_delete_link(db_session: Session):
    link = repository.create_short_link(db_session, "https://del.com", "hard-del")
    repository.delete_link(db_session, link)
    assert repository.get_link_by_code(db_session, "hard-del") is None


def test_update_link_expires_at(db_session: Session):
    link = repository.create_short_link(db_session, "https://time.com", "time-link")
    future_date = (datetime.now(UTC) + timedelta(days=10)).replace(tzinfo=None)
    updated_link = repository.update_link(db_session, link, new_expires_at=future_date)
    assert updated_link.expires_at == future_date


def test_get_popular_links(db_session: Session):
    link1 = repository.create_short_link(db_session, "https://1.com", "link1")
    link2 = repository.create_short_link(db_session, "https://2.com", "link2")
    link1.clicks = 50
    link2.clicks = 100
    db_session.commit()
    popular = repository.get_popular_links(db_session, limit=10)
    assert len(popular) == 2
    assert popular[0].short_id == "link2"
    assert popular[1].short_id == "link1"

def test_cleanup_inactive_links(db_session: Session):
    link = repository.create_short_link(db_session, "https://lazy.com", "lazy-link")
    old_date = (datetime.now(UTC) - timedelta(days=40)).replace(tzinfo=None)
    link.created_at = old_date
    link.last_clicked_at = old_date
    db_session.commit()
    deleted_count = repository.cleanup_inactive_links(db_session, days_inactive=30)
    assert deleted_count == 1
    assert link.is_active is False
    assert "inactive_for_30" in link.deletion_reason


def test_purge_soft_deleted_links(db_session: Session):
    link = repository.create_short_link(db_session, "https://trash.com", "trash-link")
    repository.soft_delete_link(db_session, link, "user_deleted")
    old_dt = (datetime.now(UTC) - timedelta(days=40)).replace(tzinfo=None)
    link.deleted_at = old_dt
    db_session.commit()

    purged_count = repository.purge_soft_deleted_links(db_session, days_since_deleted=30)
    assert purged_count == 1
    assert repository.get_link_by_code(db_session, "trash-link") is None

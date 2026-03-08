from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import Link, User


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, hashed_password: str, role: str = "user") -> User:
    db_user = User(
        username=username,
        hashed_password=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def is_alias_taken(db: Session, alias: str) -> bool:
    return db.query(Link).filter(Link.alias == alias).first() is not None

def is_short_id_taken(db: Session, short_id: str) -> bool:
    return db.query(Link).filter(Link.short_id == short_id).first() is not None

def create_short_link(
    db: Session,
    original_url: str,
    short_id: str,
    alias: str | None = None,
    user_id: int | None = None,
    expires_at: datetime | None = None
) -> Link:
    db_link = Link(
        original_url=original_url,
        short_id=short_id,
        alias=alias,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def delete_link(db: Session, link: Link):
    db.delete(link)
    db.commit()

def update_link(
    db: Session,
    link: Link,
    new_url: str | None = None,
    new_alias: str | None = None,
    new_expires_at: datetime | None = None
) -> Link:
    if new_url:
        link.original_url = new_url
    if new_alias:
        link.alias = new_alias
        link.short_id = new_alias
    if new_expires_at:
        link.expires_at = new_expires_at
    db.commit()
    db.refresh(link)
    return link

def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter((Link.short_id == code) | (Link.alias == code)).first()

def record_click(db: Session, link: Link):
    link.clicks += 1
    link.last_clicked_at = datetime.now(UTC)
    db.commit()
    db.refresh(link)

def get_links_by_original_url(db: Session, original_url: str) -> list[Link]:
    return db.query(Link).filter(Link.original_url == original_url).all()

def soft_delete_link(db: Session, link: Link, reason: str):
    link.is_active = False
    link.deletion_reason = reason
    link.deleted_at = datetime.now(UTC)
    db.commit()
    db.refresh(link)

def get_user_deleted_links(db: Session, user_id: int) -> list[Link]:
    return db.query(Link).filter(
        Link.user_id == user_id,
        not Link.is_active
    ).all()

def cleanup_inactive_links(db: Session, days_inactive: int) -> int:
    cutoff_date = datetime.now(UTC) - timedelta(days=days_inactive)
    active_links = db.query(Link).filter(Link.is_active).all()
    deleted_count = 0
    for link in active_links:
        last_activity = link.last_clicked_at if link.last_clicked_at else link.created_at
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=UTC)
        if last_activity < cutoff_date:
            soft_delete_link(db, link, reason=f"inactive_for_{days_inactive}_days")
            deleted_count += 1
    return deleted_count

def purge_soft_deleted_links(db: Session, days_since_deleted: int) -> int:
    cutoff_date = datetime.now(UTC) - timedelta(days=days_since_deleted)
    query = db.query(Link).filter(
        not Link.is_active,
        Link.deleted_at < cutoff_date
    )
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return deleted_count

def get_popular_links(db: Session, limit: int = 100) -> list[Link]:
    """Fetches the top N most clicked active links."""
    return db.query(Link).filter(
        Link.is_active
    ).order_by(Link.clicks.desc()).limit(limit).all()

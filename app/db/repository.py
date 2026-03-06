from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import User, Link

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
    if new_expires_at:
        link.expires_at = new_expires_at
    db.commit()
    db.refresh(link)
    return link

def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter((Link.short_id == code) | (Link.alias == code)).first()

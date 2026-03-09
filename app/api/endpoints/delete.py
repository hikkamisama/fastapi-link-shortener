from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import app.db.redis_cache as redis_cache
import app.db.repository as repository
import app.schemas.schema as schema
from app.core.security import authenticate
from app.db.session import get_db

router = APIRouter()

@router.delete("/cleanup/inactive")
def trigger_inactive_cleanup(
    user: Annotated[schema.User, Depends(authenticate)],
    days: int = Query(..., description="Number of days of inactivity before deletion"),
    db: Session = Depends(get_db)
):
    if not user or user.role != "admin":
         raise HTTPException(status_code=403, detail="Only admins can run cleanup tasks")
    count = repository.cleanup_inactive_links(db, days)
    return {"detail": f"Cleanup complete. {count} links were soft-deleted for inactivity."}

@router.delete("/{short_code}")
def delete_shortened_link(
    short_code: str,
    user: Annotated[schema.User, Depends(authenticate)],
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    link = repository.get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db_user = repository.get_user_by_username(db, user.username)

    if link.user_id != db_user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this link")

    repository.soft_delete_link(db, link, reason="user_deleted")
    redis_cache.redis_client.delete(f"link:{short_code}")

    return {"detail": "Link deleted successfully"}

@router.delete("/cleanup/purge")
def trigger_hard_delete_purge(
    user: Annotated[schema.User, Depends(authenticate)],
    days: int = Query(30, description="Permanently delete links soft-deleted more than N days ago"),
    db: Session = Depends(get_db)
):
    if not user or user.role != "admin":
         raise HTTPException(status_code=403, detail="Only admins can purge database records")
    count = repository.purge_soft_deleted_links(db, days)
    return {"detail": f"Database purged. {count} rows were permanently destroyed."}

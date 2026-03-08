from __future__ import annotations

import random
import string
from datetime import UTC, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl
from sqlalchemy.orm import Session

import app.db.repository as repository
import app.schemas.schema as schema
from app.core.config import DOMAIN
from app.core.security import authenticate
from app.core.tasks import background_record_click
from app.db.redis_cache import redis_client
from app.db.session import get_db

router = APIRouter()

def generate_random_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def make_naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


@router.post("/links/shorten", response_model=schema.Response)
def shorten_link(
    request: schema.LinkRequest,
    user: Annotated[Optional[schema.User], Depends(authenticate)],
    db: Session = Depends(get_db)
):
    db_user = repository.get_user_by_username(db, user.username) if user else None

    if request.alias:
        if not db_user:
            raise HTTPException(status_code=401, detail="Must be logged in to use alias.")
        if repository.is_alias_taken(db, request.alias):
            raise HTTPException(status_code=400, detail="Alias is already taken.")
        short_code = request.alias
    else:
        short_code = generate_random_short_code()
        while repository.is_short_id_taken(db, short_code):
            short_code = generate_random_short_code()

    safe_expires_at = make_naive_utc(request.expires_at)

    repository.create_short_link(
        db=db,
        original_url=str(request.url),
        short_id=short_code,
        alias=request.alias,
        user_id=db_user.id if db_user else None,
        expires_at=safe_expires_at
    )

    return schema.Response(response="Success", short_link=f"{DOMAIN}/{request.alias or short_code}")


@router.get("/links/search", response_model=list[schema.LinkSearchResult])
def search_links(
    original_url: HttpUrl = Query(..., description="The original URL to search for"),
    db: Session = Depends(get_db)
):
    url_str = str(original_url)
    links = repository.get_links_by_original_url(db, url_str)
    if not links:
        raise HTTPException(
            status_code=404,
            detail="No shortened links found for this URL"
        )
    return links

@router.get("/links/history/deleted",response_model=list[schema.DeletedLinkInfo])
def get_deleted_history(
    user: Annotated[schema.User, Depends(authenticate)],
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db_user = repository.get_user_by_username(db, user.username)
    history = repository.get_user_deleted_links(db, db_user.id)

    return history


@router.delete("/links/cleanup/inactive")
def trigger_inactive_cleanup(
    user: Annotated[schema.User, Depends(authenticate)],
    days: int = Query(..., description="Number of days of inactivity before deletion"),
    db: Session = Depends(get_db)
):
    if not user or user.role != "admin":
         raise HTTPException(status_code=403, detail="Only admins can run cleanup tasks")
    count = repository.cleanup_inactive_links(db, days)
    return {"detail": f"Cleanup complete. {count} links were soft-deleted for inactivity."}


@router.get("/links/{short_code}")
def redirect_to_original(
    short_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    cache_key = f"link:{short_code}"
    cached_url = redis_client.get(cache_key)
    if cached_url:
        background_tasks.add_task(background_record_click, short_code)
        return RedirectResponse(url=cached_url)

    link = repository.get_link_by_code(db, short_code)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if not link.is_active:
        raise HTTPException(
            status_code=410,
            detail=f"This link is no longer active. Reason: {link.deletion_reason}"
        )

    if link.expires_at:
        expire_time = link.expires_at
        if expire_time.tzinfo is None:
            expire_time = expire_time.replace(tzinfo=UTC)
        if expire_time < datetime.now(UTC):
            repository.soft_delete_link(db, link, reason="expired")
            raise HTTPException(status_code=410, detail="This link has expired")

    repository.record_click(db, link)
    if link.clicks >= 20:
        redis_client.setex(cache_key, 86400, link.original_url)

    return RedirectResponse(url=link.original_url)


@router.delete("/links/{short_code}")
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
    redis_client.delete(f"link:{short_code}")

    return {"detail": "Link deleted successfully"}


@router.put("/links/{short_code}")
def update_shortened_link(
    short_code: str,
    request: schema.LinkUpdateRequest,
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
        raise HTTPException(status_code=403, detail="Not authorized to update this link")

    if request.short_code and request.short_code != short_code:
        if repository.is_alias_taken(db, request.short_code) or \
           repository.is_short_id_taken(db, request.short_code):
            raise HTTPException(status_code=400, detail="The new short code is already taken")

    safe_expires_at = make_naive_utc(request.expires_at)

    repository.update_link(
        db=db,
        link=link,
        new_url=str(request.original_url) if request.original_url else None,
        new_alias=request.short_code,
        new_expires_at=safe_expires_at
    )
    redis_client.delete(f"link:{short_code}")

    return {
        "detail": "Link updated successfully", "new_link": f"{DOMAIN}/{link.alias or link.short_id}"
    }


@router.get("/links/{short_code}/stats", response_model=schema.LinkStats)
def get_link_stats(
    short_code: str,
    user: Annotated[schema.User, Depends(authenticate)],
    db: Session = Depends(get_db)):
    link = repository.get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db_user = repository.get_user_by_username(db, user.username)

    if link.user_id != db_user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view these stats")
    return link


@router.delete("/links/cleanup/purge")
def trigger_hard_delete_purge(
    user: Annotated[schema.User, Depends(authenticate)],
    days: int = Query(30, description="Permanently delete links soft-deleted more than N days ago"),
    db: Session = Depends(get_db)
):
    if not user or user.role != "admin":
         raise HTTPException(status_code=403, detail="Only admins can purge database records")
    count = repository.purge_soft_deleted_links(db, days)
    return {"detail": f"Database purged. {count} rows were permanently destroyed."}

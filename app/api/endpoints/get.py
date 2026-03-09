from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import app.db.redis_cache as redis_cache
import app.db.repository as repository
from app.core.tasks import background_record_click
from app.db.session import get_db

router = APIRouter()

@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    cache_key = f"link:{short_code}"
    cached_url = redis_cache.redis_client.get(cache_key)
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
        redis_cache.redis_client.setex(cache_key, 86400, link.original_url)

    return RedirectResponse(url=link.original_url)

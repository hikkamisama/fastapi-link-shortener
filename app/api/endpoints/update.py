from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.core.helpers as helpers
import app.db.redis_cache as redis_cache
import app.db.repository as repository
import app.schemas.schema as schema
from app.core.config import DOMAIN
from app.core.security import authenticate
from app.db.session import get_db

router = APIRouter()

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

    safe_expires_at = helpers.make_naive_utc(request.expires_at)

    repository.update_link(
        db=db,
        link=link,
        new_url=str(request.original_url) if request.original_url else None,
        new_alias=request.short_code,
        new_expires_at=safe_expires_at
    )
    redis_cache.redis_client.delete(f"link:{short_code}")

    return {
        "detail": "Link updated successfully", "new_link": f"{DOMAIN}/{link.alias or link.short_id}"
    }


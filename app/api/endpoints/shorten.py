from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.core.helpers as helpers
import app.db.repository as repository
import app.schemas.schema as schema
from app.core.config import DOMAIN
from app.core.security import authenticate
from app.db.session import get_db

router = APIRouter()

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
        short_code = helpers.generate_random_short_code()
        while repository.is_short_id_taken(db, short_code):
            short_code = helpers.generate_random_short_code()

    safe_expires_at = helpers.make_naive_utc(request.expires_at)

    repository.create_short_link(
        db=db,
        original_url=str(request.url),
        short_id=short_code,
        alias=request.alias,
        user_id=db_user.id if db_user else None,
        expires_at=safe_expires_at
    )

    return schema.Response(response="Success", short_link=f"{DOMAIN}/{request.alias or short_code}")

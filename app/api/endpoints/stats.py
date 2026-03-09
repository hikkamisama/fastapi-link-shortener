from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.db.repository as repository
import app.schemas.schema as schema
from app.core.security import authenticate
from app.db.session import get_db

router = APIRouter()

@router.get("/{short_code}/stats", response_model=schema.LinkStats)
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

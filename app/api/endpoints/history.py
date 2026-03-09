from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.db.repository as repository
import app.schemas.schema as schema
from app.core.security import authenticate
from app.db.session import get_db

router = APIRouter()

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

from __future__ import annotations
from typing import Annotated, Optional
import random
import string
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.core.config import DOMAIN
from app.core.security import authenticate
from app.db.session import get_db
import app.db.repository as repository
import app.schemas.schema as schema

router = APIRouter()

def generate_random_shortcode(length: int = 6) -> str:
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
        shortcode = request.alias
    else:
        shortcode = generate_random_shortcode() 
        while repository.is_short_id_taken(db, shortcode):
            shortcode = generate_random_shortcode()
    
    safe_expires_at = make_naive_utc(request.expires_at)

    repository.create_short_link(
        db=db, 
        original_url=str(request.url), 
        short_id=shortcode, 
        alias=request.alias,
        user_id=db_user.id if db_user else None,
        expires_at=safe_expires_at
    )

    return schema.Response(response="Success", short_link=f"{DOMAIN}/{request.alias or shortcode}")


@router.get("/links/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    link = repository.get_link_by_code(db, short_code)
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.expires_at:
        expire_time = link.expires_at
        if expire_time.tzinfo is None:
            expire_time = expire_time.replace(tzinfo=UTC)
        if expire_time < datetime.now(UTC):
            raise HTTPException(status_code=410, detail="This link has expired")

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

    repository.delete_link(db, link)
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
        if repository.is_alias_taken(db, request.short_code) or repository.is_short_id_taken(db, request.short_code):
            raise HTTPException(status_code=400, detail="The new short code is already taken")

    repository.update_link(
        db=db,
        link=link,
        new_url=str(request.original_url) if request.original_url else None,
        new_alias=request.short_code,
        new_expires_at=request.expires_at
    )

    return {"detail": "Link updated successfully", "new_link": f"{DOMAIN}/{link.alias or link.short_id}"}

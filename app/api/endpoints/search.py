from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import HttpUrl
from sqlalchemy.orm import Session

import app.db.repository as repository
import app.schemas.schema as schema
from app.db.session import get_db

router = APIRouter()

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

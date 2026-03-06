from datetime import datetime
from pydantic import BaseModel, HttpUrl

class LinkRequest(BaseModel):
    url: HttpUrl
    alias: str | None = None
    expires_at: datetime | None = None

class LinkUpdateRequest(BaseModel):
    original_url: HttpUrl | None = None
    short_code: str | None = None       
    expires_at: datetime | None = None

class Response(BaseModel):
    response: str
    short_link: str | None = None

class User(BaseModel):
    username: str
    role: str

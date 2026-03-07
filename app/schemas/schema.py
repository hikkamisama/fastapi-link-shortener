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

class LoginRequest(BaseModel):
    username: str
    password: str

class Response(BaseModel):
    response: str
    short_link: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    model_config = {"from_attributes": True}

class User(BaseModel):
    username: str
    role: str

import re
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, field_validator
from app.core.config import RESERVED_WORDS

class LinkRequest(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    expires_at: datetime | None = Field(default=None, json_schema_extra={"example": None})

    @field_validator("alias")
    @classmethod
    def check_reserved_words(cls, value: str | None) -> str | None:
        if value and value.lower() in RESERVED_WORDS:
            raise ValueError(f"The alias '{value}' is reserved and cannot be used.")
        return value

class LinkUpdateRequest(BaseModel):
    original_url: HttpUrl | None = None
    short_code: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    expires_at: datetime | None = Field(default=None, json_schema_extra={"example": None})

    @field_validator("short_code")
    @classmethod
    def check_reserved_words(cls, value: str | None) -> str | None:
        if value and value.lower() in RESERVED_WORDS:
            raise ValueError(f"The short code '{value}' is reserved and cannot be used.")
        return value

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

from typing import Optional
from datetime import datetime, UTC
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_url: Mapped[str] = mapped_column(String(2048))
    short_id: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    alias: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    owner: Mapped[Optional["User"]] = relationship(back_populates="links")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")

    links: Mapped[list["Link"]] = relationship(back_populates="owner")

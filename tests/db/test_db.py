import importlib
from unittest.mock import patch

import pytest
from pydantic import ValidationError

import app.core.config
from app.db.session import get_db
from app.schemas.schema import (
    LinkRequest,
    LinkUpdateRequest,
)


def test_schema_reserved_word_validation_create():
    with pytest.raises(ValidationError) as exc_info:
        LinkRequest(url="https://docs.com", alias="admin")
    assert "reserved and cannot be used" in str(exc_info.value)

def test_schema_reserved_word_validation_update():
    with pytest.raises(ValidationError) as exc_info:
        LinkUpdateRequest(original_url="https://docs.com", short_code="login")
    assert "reserved and cannot be used" in str(exc_info.value)

def test_get_db_generator():
    db_generator = get_db()
    db_session = next(db_generator)
    assert db_session is not None
    with pytest.raises(StopIteration):
        next(db_generator)

def test_session_engine_creation_postgres():
    original_url = app.core.config.DATABASE_URL
    try:
        app.core.config.DATABASE_URL = "postgres://user:pass@localhost/db"
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            importlib.reload(app.db.session)
            mock_create_engine.assert_called_once_with(
                "postgresql://user:pass@localhost/db",
                pool_size=20,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
    finally:
        app.core.config.DATABASE_URL = original_url
        importlib.reload(app.db.session)

def test_session_engine_creation_other_db():
    original_url = app.core.config.DATABASE_URL
    try:
        app.core.config.DATABASE_URL = "mysql://user:pass@localhost/db"
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            importlib.reload(app.db.session)
            mock_create_engine.assert_called_once_with(
                "mysql://user:pass@localhost/db",
                pool_size=20,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )

    finally:
        app.core.config.DATABASE_URL = original_url
        importlib.reload(app.db.session)

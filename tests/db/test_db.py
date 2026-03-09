import pytest
from pydantic import ValidationError

from app.db.session import get_db
from app.schemas.schema import (
    LinkRequest,  # Update path if your schema file is named differently!
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

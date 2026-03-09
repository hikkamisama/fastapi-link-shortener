import jwt
import pytest
from pydantic import ValidationError

import app.core.security as security
from app.core.config import SECRET_KEY
from app.schemas.schema import LinkRequest


def test_password_hashing():
    password = "supersecretpassword"
    hashed = security.get_password_hash(password)

    assert password != hashed
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrongpassword", hashed) is False

def test_schema_reserved_words_validation():
    with pytest.raises(ValidationError) as excinfo:
        LinkRequest(url="https://google.com", alias="login")
    assert "reserved and cannot be used" in str(excinfo.value)

def test_schema_invalid_characters_validation():
    with pytest.raises(ValidationError):
        LinkRequest(url="https://google.com", alias="my alias!")

def test_authenticate_invalid_payload(client):
    bad_token = jwt.encode({"role": "user"}, SECRET_KEY, algorithm="HS256")
    res = client.get("/links/history/deleted", headers={"Authorization": f"Bearer {bad_token}"})
    assert res.status_code == 401
    assert "Invalid token payload" in res.json()["detail"]

def test_authenticate_jwt_error(client):
    res = client.get(
        "/links/history/deleted",
        headers={"Authorization": "Bearer thisISnotArealTOKEN!!"}
    )
    assert res.status_code == 401
    assert "Could not validate credentials" in res.json()["detail"]

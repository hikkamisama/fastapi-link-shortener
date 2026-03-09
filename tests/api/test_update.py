import app.core.security as security
import app.db.repository as repository


def test_update_unauthorized(client):
    res = client.put("/links/somecode", json={})
    assert res.status_code == 401

def test_update_not_found(client, auth_header):
    res = client.put("/links/fakecode", json={}, headers=auth_header)
    assert res.status_code == 404

def test_update_success(client, auth_header):
    client.post(
        "/links/shorten",
        json={"url": "https://old.com", "alias": "up-link"},
        headers=auth_header
    )
    payload = {"original_url": "https://new.com", "short_code": "new-link"}
    res = client.put("/links/up-link", json=payload, headers=auth_header)
    assert res.status_code == 200
    assert "new-link" in res.json()["new_link"]
    get_res = client.get("/new-link", follow_redirects=False)
    assert get_res.headers["location"] == "https://new.com/"

def test_update_alias_already_taken(client, auth_header):
    client.post(
        "/links/shorten",
        json={"url": "https://a.com", "alias": "alpha"},
        headers=auth_header
    )
    client.post(
        "/links/shorten",
        json={"url": "https://b.com", "alias": "beta"},
        headers=auth_header
    )
    res = client.put("/links/alpha", json={"short_code": "beta"}, headers=auth_header)
    assert res.status_code == 400
    assert "taken" in res.json()["detail"].lower()

def test_update_forbidden_other_user(client, auth_header, db_session):
    client.post(
        "/links/shorten",
        json={"url": "https://a.com", "alias": "a-link"},
        headers=auth_header
    )
    _= repository.create_user(db_session, "user_b_put", security.get_password_hash("pass"))
    token_b = security.create_access_token({"sub": "user_b_put", "role": "user"})
    auth_b = {"Authorization": f"Bearer {token_b}"}
    res = client.put("/links/a-link", json={"short_code": "stolen"}, headers=auth_b)
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]

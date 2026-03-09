import app.core.security as security
import app.db.repository as repository


def test_rerouting_deleted_link(client, auth_header):
    client.post(
        "/links/shorten",
        json={"url": "https://bing.com", "alias": "bing"},
        headers=auth_header
    )
    client.delete("/links/bing", headers=auth_header)
    response = client.get("/bing")
    assert response.status_code == 410
    assert "user_deleted" in response.json()["detail"]

def test_trigger_inactive_cleanup_forbidden(client, auth_header):
    response = client.delete("/links/cleanup/inactive?days=30", headers=auth_header)
    assert response.status_code == 403
    assert "Only admins" in response.json()["detail"]

def test_trigger_inactive_cleanup_admin(client, db_session):
    admin_user = repository.create_user(
        db_session,
        username="admin_tester",
        hashed_password=security.get_password_hash("password")
    )
    admin_user.role = "admin"
    db_session.commit()
    admin_token = security.create_access_token(
        {"sub": admin_user.username, "role": admin_user.role}
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.delete("/links/cleanup/inactive?days=30", headers=admin_headers)
    assert response.status_code == 200
    assert "Cleanup complete" in response.json()["detail"]

def test_delete_unauthorized(client):
    """Hits the 'if not user -> 401' block."""
    res = client.delete("/links/anycode")
    assert res.status_code == 401


def test_delete_not_found(client, auth_header):
    """Hits the 'if not link -> 404' block."""
    res = client.delete("/links/ghost-code", headers=auth_header)
    assert res.status_code == 404


def test_delete_forbidden_other_user(client, auth_header, db_session):
    _ = repository.create_user(db_session, "user_b", security.get_password_hash("pass"))
    token_b = security.create_access_token({"sub": "user_b", "role": "user"})
    auth_b = {"Authorization": f"Bearer {token_b}"}
    client.post("/links/shorten", json={"url": "https://b.com", "alias": "b-link"}, headers=auth_b)
    res = client.delete("/links/b-link", headers=auth_header)
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]

def test_trigger_hard_delete_purge_forbidden(client, auth_header):
    res = client.delete("/links/cleanup/purge?days=30", headers=auth_header)
    assert res.status_code == 403
    assert "Only admins" in res.json()["detail"]

def test_trigger_hard_delete_purge_admin(client, db_session):
    admin_user = repository.create_user(
        db_session, "admin_purger",
        security.get_password_hash("pass")
    )
    admin_user.role = "admin"
    db_session.commit()
    admin_token = security.create_access_token({"sub": admin_user.username, "role": "admin"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.delete("/links/cleanup/purge?days=30", headers=admin_headers)
    assert res.status_code == 200
    assert "Database purged" in res.json()["detail"]

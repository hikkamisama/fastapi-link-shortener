import app.core.security as security
import app.db.repository as repository


def test_get_stats_success(client, auth_header):
    client.post(
        "/links/shorten",
        json={"url": "https://datatester.com", "alias": "stats-link"},
        headers=auth_header
    )
    client.get("/stats-link", follow_redirects=False)
    client.get("/stats-link", follow_redirects=False)
    client.get("/stats-link", follow_redirects=False)
    response = client.get("/links/stats-link/stats", headers=auth_header)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["original_url"] == "https://datatester.com/"
    assert data["clicks"] == 3

def test_get_stats_not_found(client, auth_header):
    response = client.get("/links/never-existed/stats", headers=auth_header)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_stats_forbidden(client, auth_header, db_session):
    _ = repository.create_user(db_session, "stats_user", security.get_password_hash("pass"))
    token_b = security.create_access_token({"sub": "stats_user", "role": "user"})
    auth_b = {"Authorization": f"Bearer {token_b}"}
    client.post(
        "/links/shorten",
        json={"url": "https://secret.com", "alias": "secret-stats"},
        headers=auth_b
    )
    response = client.get("/links/secret-stats/stats", headers=auth_header)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

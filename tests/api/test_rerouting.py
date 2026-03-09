from datetime import UTC, datetime, timedelta


def test_rerouting_success(client, auth_header):
    client.post(
        "/links/shorten",
        json={"url": "https://github.com", "alias": "git"},
        headers=auth_header
    )
    response = client.get("/git", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://github.com/"

def test_rerouting_expired_link(client, auth_header):
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    post_response = client.post(
        "/links/shorten",
        json={"url": "https://github.com", "alias": "expired-git", "expires_at": yesterday},
        headers=auth_header
    )
    assert post_response.status_code == 200, post_response.json()
    response = client.get("/expired-git")
    assert response.status_code == 410
    assert "expired" in response.json()["detail"]

from unittest.mock import patch


def test_create_link_api(client, auth_header):
    payload = {"url": "https://fastapi.tiangolo.com/", "alias": "fastapi-docs"}
    response = client.post("/links/shorten", json=payload, headers=auth_header)

    assert response.status_code == 200
    assert "fastapi-docs" in response.json()["short_link"]

def test_invalid_data_api(client, auth_header):
    payload = {"url": "not-a-real-url"}
    response = client.post("/links/shorten", json=payload, headers=auth_header)

    assert response.status_code == 422


def test_shorten_link_unauthorized(client):
    response = client.post(
        "/links/shorten",
        json={"url": "https://google.com", "alias": "my-google"}
    )
    assert response.status_code == 401
    assert "Must be logged in to use alias." in response.json()["detail"]

def test_shorten_link_alias_already_taken(client, auth_header):
    res1 = client.post(
        "/links/shorten",
        json={"url": "https://github.com", "alias": "claimed"},
        headers=auth_header
    )
    assert res1.status_code == 200
    res2 = client.post(
        "/links/shorten",
        json={"url": "https://yahoo.com", "alias": "claimed"},
        headers=auth_header
    )
    assert res2.status_code == 400
    assert "taken" in res2.json()["detail"].lower()

def test_shorten_link_no_alias(client):
    response = client.post(
        "/links/shorten",
        json={"url": "https://python.org"}
    )
    assert response.status_code == 200
    assert "Success" in response.json()["response"]

def test_shorten_link_collision_loop(client):
    with patch("app.core.helpers.generate_random_short_code", side_effect=["TAKEN_ID", "FREE_ID"]):
        with patch("app.db.repository.is_short_id_taken", side_effect=[True, False]):
            response = client.post(
                "/links/shorten",
                json={"url": "https://python.org"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "FREE_ID" in data["short_link"]
            assert "TAKEN_ID" not in data["short_link"]

def test_get_deleted_history_unauthorized(client):
    response = client.get("/links/history/deleted")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_get_deleted_history(client, auth_header):
    history_empty = client.get("/links/history/deleted", headers=auth_header)
    assert history_empty.status_code == 200, history_empty.json()
    assert len(history_empty.json()) == 0
    post_res = client.post(
        "/links/shorten",
        json={"url": "https://reddit.com/", "alias": "del-me"},
        headers=auth_header
    )
    assert post_res.status_code == 200, post_res.json()
    del_res = client.delete("/links/del-me", headers=auth_header)
    assert del_res.status_code == 200, del_res.json()
    history_full = client.get("/links/history/deleted", headers=auth_header)
    assert history_full.status_code == 200, history_full.json()
    data = history_full.json()
    assert len(data) == 1, f"Expected 1 link in history, but got: {data}"

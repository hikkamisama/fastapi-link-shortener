def test_search_links_success_and_fail(client, auth_header):
    post1 = client.post(
        "/links/shorten",
        json={"url": "https://youtube.com/", "alias": "yt-1"},
        headers=auth_header
    )
    assert post1.status_code == 200, post1.json()
    post2 = client.post(
        "/links/shorten",
        json={"url": "https://youtube.com/", "alias": "yt-2"},
        headers=auth_header
    )
    assert post2.status_code == 200, post2.json()
    res_success = client.get("/links/search?original_url=https://youtube.com/")
    assert res_success.status_code == 200, res_success.json()
    data = res_success.json()
    assert len(data) == 2
    assert data[0]["alias"] == "yt-1"
    assert data[1]["alias"] == "yt-2"
    res_fail = client.get("/links/search?original_url=https://doesnotexist.com")
    assert res_fail.status_code == 404
    assert "No shortened links found" in res_fail.json()["detail"]

def test_redirect_not_found(client):
    """Hits the 'if not link -> 404' block."""
    res = client.get("/links/nonexistent-code", follow_redirects=False)
    assert res.status_code == 404

def test_redirect_inactive(client, auth_header):
    client.post(
        "/links/shorten",
        json={"url": "https://example.com", "alias": "dead-link"},
        headers=auth_header
    )
    client.delete("/links/dead-link", headers=auth_header)
    res = client.get("/links/dead-link", follow_redirects=False)
    assert res.status_code == 410
    assert "no longer active" in res.json()["detail"].lower()

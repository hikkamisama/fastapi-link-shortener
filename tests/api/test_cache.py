from unittest.mock import patch


def test_redirect_cache_hit(client):
    with patch("app.db.redis_cache.redis_client") as mock_redis:
        mock_redis.get.return_value = "https://lightning-fast.com"
        res = client.get("/fake-code-but-cached", follow_redirects=False)
        assert res.status_code == 307
        assert res.headers["location"] == "https://lightning-fast.com"

def test_redirect_viral_cache(client, auth_header, db_session, mock_redis):
    """Hits the 'if link.clicks >= 20:' block."""
    client.post(
        "/links/shorten",
        json={"url": "https://viral.com", "alias": "viral"},
        headers=auth_header
    )
    from app.db.models import Link
    link = db_session.query(Link).filter(Link.alias == "viral").first()
    link.clicks = 19
    db_session.commit()
    client.get("/viral", follow_redirects=False)
    mock_redis.setex.assert_called_once_with("link:viral", 86400, "https://viral.com/")

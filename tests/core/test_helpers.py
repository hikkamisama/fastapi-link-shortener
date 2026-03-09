from datetime import UTC, datetime

import app.core.helpers as helpers


def test_make_naive_utc_already_naive():
    dt = datetime(2025, 1, 1)
    assert helpers.make_naive_utc(dt) == dt

def test_make_naive_utc():
    aware_dt = datetime.now(UTC)
    naive_dt = helpers.make_naive_utc(aware_dt)
    assert naive_dt.tzinfo is None

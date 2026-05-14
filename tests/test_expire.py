"""Tests for envchain.expire."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from envchain import expire as exp
from envchain.expire import ExpireError, set_expiry, get_expiry, clear_expiry, is_expired, list_expiry


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path)
    monkeypatch.setattr("envchain.expire._store_dir", lambda: tmp_path)
    yield tmp_path


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def test_set_expiry_returns_datetime():
    dt = _future()
    result = set_expiry("myapp", dt)
    assert isinstance(result, datetime)
    assert result == dt


def test_get_expiry_returns_none_when_not_set():
    assert get_expiry("nonexistent") is None


def test_set_and_get_roundtrip():
    dt = _future(7200)
    set_expiry("proj", dt)
    retrieved = get_expiry("proj")
    assert retrieved is not None
    # Compare ignoring sub-microsecond rounding from ISO serialisation
    assert abs((retrieved - dt).total_seconds()) < 1


def test_set_expiry_in_past_raises():
    with pytest.raises(ExpireError, match="future"):
        set_expiry("proj", _past())


def test_set_expiry_naive_datetime_treated_as_utc():
    naive = datetime.utcnow() + timedelta(hours=1)
    result = set_expiry("proj", naive)
    assert result.tzinfo is not None


def test_is_expired_false_when_not_set():
    assert is_expired("proj") is False


def test_is_expired_false_before_expiry():
    set_expiry("proj", _future(3600))
    assert is_expired("proj") is False


def test_is_expired_true_after_expiry():
    fixed_future = _future(1)
    set_expiry("proj", fixed_future)
    # Simulate time passing beyond the expiry
    far_future = datetime.now(timezone.utc) + timedelta(hours=2)
    with patch.object(exp, "_now", return_value=far_future):
        assert is_expired("proj") is True


def test_clear_expiry_returns_true_when_removed():
    set_expiry("proj", _future())
    assert clear_expiry("proj") is True
    assert get_expiry("proj") is None


def test_clear_expiry_returns_false_when_not_set():
    assert clear_expiry("unknown") is False


def test_list_expiry_empty():
    assert list_expiry() == {}


def test_list_expiry_multiple_profiles():
    dt1 = _future(1000)
    dt2 = _future(2000)
    set_expiry("alpha", dt1)
    set_expiry("beta", dt2)
    result = list_expiry()
    assert set(result.keys()) == {"alpha", "beta"}
    assert isinstance(result["alpha"], datetime)

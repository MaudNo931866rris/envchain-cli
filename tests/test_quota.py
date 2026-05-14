"""Tests for envchain.quota."""

from __future__ import annotations

import pytest

from envchain.quota import (
    QuotaError,
    QuotaPolicy,
    check_quota,
    clear_quota,
    get_quota,
    set_quota,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store.STORE_DIR", str(tmp_path))
    monkeypatch.setattr("envchain.quota._store_dir", lambda: tmp_path)
    return tmp_path


def test_get_quota_returns_none_when_not_set():
    assert get_quota("myproject") is None


def test_set_and_get_roundtrip():
    policy = QuotaPolicy(max_vars=10, max_value_bytes=512, max_total_bytes=2048)
    set_quota("myproject", policy)
    loaded = get_quota("myproject")
    assert loaded is not None
    assert loaded.max_vars == 10
    assert loaded.max_value_bytes == 512
    assert loaded.max_total_bytes == 2048


def test_set_quota_empty_profile_raises():
    with pytest.raises(QuotaError, match="empty"):
        set_quota("", QuotaPolicy())


def test_clear_quota_removes_entry():
    set_quota("proj", QuotaPolicy())
    clear_quota("proj")
    assert get_quota("proj") is None


def test_clear_quota_nonexistent_is_noop():
    clear_quota("does_not_exist")  # should not raise


def test_check_quota_no_policy_passes():
    check_quota("unset", {"KEY": "value"})


def test_check_quota_within_limits_passes():
    set_quota("proj", QuotaPolicy(max_vars=5, max_value_bytes=100, max_total_bytes=500))
    check_quota("proj", {"A": "1", "B": "2"})


def test_check_quota_exceeds_max_vars_raises():
    set_quota("proj", QuotaPolicy(max_vars=2))
    with pytest.raises(QuotaError, match="max variable count"):
        check_quota("proj", {"A": "1", "B": "2", "C": "3"})


def test_check_quota_exceeds_max_value_bytes_raises():
    set_quota("proj", QuotaPolicy(max_value_bytes=5))
    with pytest.raises(QuotaError, match="max value size"):
        check_quota("proj", {"KEY": "toolongvalue"})


def test_check_quota_exceeds_max_total_bytes_raises():
    set_quota("proj", QuotaPolicy(max_total_bytes=10))
    with pytest.raises(QuotaError, match="max total size"):
        check_quota("proj", {"A": "12345", "B": "67890"})


def test_set_quota_overwrites_existing():
    set_quota("proj", QuotaPolicy(max_vars=10))
    set_quota("proj", QuotaPolicy(max_vars=50))
    assert get_quota("proj").max_vars == 50

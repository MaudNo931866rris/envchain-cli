"""Tests for envchain.ttl and envchain.cli_ttl."""

from __future__ import annotations

import argparse
import time
import pytest

from envchain.ttl import (
    TTLError,
    set_ttl,
    get_ttl,
    clear_ttl,
    is_expired,
    list_ttls,
)
from envchain.cli_ttl import cmd_ttl_set, cmd_ttl_clear, cmd_ttl_status, cmd_ttl_list


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def _args(**kwargs):
    ns = argparse.Namespace(**kwargs)
    return ns


# --- unit tests for ttl module ---

def test_set_ttl_returns_future_datetime():
    from datetime import timezone
    expiry = set_ttl("myproject", 3600)
    from datetime import datetime
    assert expiry > datetime.now(tz=timezone.utc)


def test_get_ttl_returns_none_when_not_set():
    assert get_ttl("ghost") is None


def test_set_and_get_roundtrip():
    expiry = set_ttl("proj", 60)
    retrieved = get_ttl("proj")
    assert retrieved is not None
    assert abs((expiry - retrieved).total_seconds()) < 1


def test_is_expired_false_for_future():
    set_ttl("future", 9999)
    assert not is_expired("future")


def test_is_expired_true_for_past():
    set_ttl("past", 1)
    time.sleep(1.05)
    assert is_expired("past")


def test_is_expired_false_when_no_ttl():
    assert not is_expired("no_ttl_profile")


def test_clear_ttl_removes_entry():
    set_ttl("temp", 120)
    removed = clear_ttl("temp")
    assert removed is True
    assert get_ttl("temp") is None


def test_clear_ttl_returns_false_when_missing():
    assert clear_ttl("nonexistent") is False


def test_list_ttls_returns_all_entries():
    set_ttl("alpha", 100)
    set_ttl("beta", 200)
    entries = list_ttls()
    assert "alpha" in entries
    assert "beta" in entries


def test_set_ttl_zero_seconds_raises():
    with pytest.raises(TTLError):
        set_ttl("bad", 0)


def test_set_ttl_negative_seconds_raises():
    with pytest.raises(TTLError):
        set_ttl("bad", -10)


# --- CLI command tests ---

def test_cmd_ttl_set_returns_zero():
    assert cmd_ttl_set(_args(profile="p1", seconds=300)) == 0


def test_cmd_ttl_set_invalid_seconds_returns_one():
    assert cmd_ttl_set(_args(profile="p1", seconds=-1)) == 1


def test_cmd_ttl_clear_returns_zero_when_exists():
    set_ttl("clr", 60)
    assert cmd_ttl_clear(_args(profile="clr")) == 0


def test_cmd_ttl_clear_returns_zero_when_missing():
    assert cmd_ttl_clear(_args(profile="ghost")) == 0


def test_cmd_ttl_status_returns_zero():
    set_ttl("st", 60)
    assert cmd_ttl_status(_args(profile="st")) == 0


def test_cmd_ttl_list_returns_zero():
    set_ttl("listed", 60)
    assert cmd_ttl_list(_args()) == 0

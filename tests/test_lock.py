"""Tests for envchain.lock and envchain.cli_lock."""

from __future__ import annotations

import time
import types
import pytest

from envchain import lock as lock_mod
from envchain.lock import LockError, get_lock_info, is_locked, lock_profile, unlock_profile
from envchain.cli_lock import cmd_lock, cmd_lock_status, cmd_unlock


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(lock_mod, "_store_dir", lambda: tmp_path)
    yield tmp_path


def _args(**kwargs):
    ns = types.SimpleNamespace(reason="", ttl=3600)
    ns.__dict__.update(kwargs)
    return ns


# --- lock_profile / unlock_profile / is_locked ---

def test_lock_creates_lock_file(isolated_store):
    lock_profile("myapp")
    assert (isolated_store / "myapp.lock").exists()


def test_is_locked_true_after_lock(isolated_store):
    lock_profile("myapp")
    assert is_locked("myapp") is True


def test_is_locked_false_before_lock(isolated_store):
    assert is_locked("myapp") is False


def test_unlock_removes_lock_file(isolated_store):
    lock_profile("myapp")
    unlock_profile("myapp")
    assert not (isolated_store / "myapp.lock").exists()


def test_is_locked_false_after_unlock(isolated_store):
    lock_profile("myapp")
    unlock_profile("myapp")
    assert is_locked("myapp") is False


def test_double_lock_raises(isolated_store):
    lock_profile("myapp")
    with pytest.raises(LockError, match="already locked"):
        lock_profile("myapp")


def test_unlock_not_locked_raises(isolated_store):
    with pytest.raises(LockError, match="not locked"):
        unlock_profile("myapp")


def test_expired_lock_treated_as_unlocked(isolated_store, monkeypatch):
    lock_profile("myapp", ttl_seconds=1)
    monkeypatch.setattr(lock_mod, "_now", lambda: time.time() + 9999)
    assert is_locked("myapp") is False


def test_get_lock_info_returns_metadata(isolated_store):
    lock_profile("myapp", reason="maintenance", ttl_seconds=600)
    info = get_lock_info("myapp")
    assert info is not None
    assert info["reason"] == "maintenance"
    assert info["ttl_seconds"] == 600
    assert info["profile"] == "myapp"


def test_get_lock_info_none_when_not_locked(isolated_store):
    assert get_lock_info("myapp") is None


# --- CLI commands ---

def test_cmd_lock_returns_zero(isolated_store, capsys):
    rc = cmd_lock(_args(profile="myapp", reason="deploy", ttl=300))
    assert rc == 0
    out = capsys.readouterr().out
    assert "locked" in out


def test_cmd_lock_double_returns_one(isolated_store, capsys):
    cmd_lock(_args(profile="myapp"))
    rc = cmd_lock(_args(profile="myapp"))
    assert rc == 1


def test_cmd_unlock_returns_zero(isolated_store, capsys):
    lock_profile("myapp")
    rc = cmd_unlock(_args(profile="myapp"))
    assert rc == 0


def test_cmd_unlock_not_locked_returns_one(isolated_store, capsys):
    rc = cmd_unlock(_args(profile="myapp"))
    assert rc == 1


def test_cmd_lock_status_locked(isolated_store, capsys):
    lock_profile("myapp", reason="ci")
    rc = cmd_lock_status(_args(profile="myapp"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "LOCKED" in out
    assert "ci" in out


def test_cmd_lock_status_not_locked(isolated_store, capsys):
    rc = cmd_lock_status(_args(profile="myapp"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "not locked" in out

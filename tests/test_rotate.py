"""Tests for envchain.rotate."""

from __future__ import annotations

import pytest

from envchain.store import save_profile, load_profile
from envchain.lock import lock_profile
from envchain.rotate import RotateError, rotate_passphrase


OLD_PASS = "OldPass1!"
NEW_PASS = "NewPass2@"
PROFILE = "myproject"
VARS = {"DB_URL": "postgres://localhost/db", "SECRET": "s3cr3t"}


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path)
    monkeypatch.setattr("envchain.lock._lock_path", lambda name: tmp_path / f"{name}.lock")
    monkeypatch.setattr("envchain.audit._log_path", lambda: tmp_path / "audit.log")
    return tmp_path


def _seed(isolated_store):
    save_profile(PROFILE, VARS, OLD_PASS)


def test_rotate_allows_load_with_new_passphrase(isolated_store):
    _seed(isolated_store)
    rotate_passphrase(PROFILE, OLD_PASS, NEW_PASS)
    data = load_profile(PROFILE, NEW_PASS)
    assert data == VARS


def test_rotate_old_passphrase_no_longer_works(isolated_store):
    _seed(isolated_store)
    rotate_passphrase(PROFILE, OLD_PASS, NEW_PASS)
    with pytest.raises(Exception):
        load_profile(PROFILE, OLD_PASS)


def test_rotate_same_passphrase_raises(isolated_store):
    _seed(isolated_store)
    with pytest.raises(RotateError, match="must differ"):
        rotate_passphrase(PROFILE, OLD_PASS, OLD_PASS)


def test_rotate_wrong_old_passphrase_raises(isolated_store):
    _seed(isolated_store)
    with pytest.raises(RotateError, match="Could not decrypt"):
        rotate_passphrase(PROFILE, "WrongPass9!", NEW_PASS)


def test_rotate_locked_profile_raises(isolated_store):
    _seed(isolated_store)
    lock_profile(PROFILE)
    with pytest.raises(RotateError, match="locked"):
        rotate_passphrase(PROFILE, OLD_PASS, NEW_PASS)


def test_rotate_records_audit_event(isolated_store):
    from envchain.audit import read_events

    _seed(isolated_store)
    rotate_passphrase(PROFILE, OLD_PASS, NEW_PASS)
    events = read_events(profile=PROFILE)
    assert any(e["event"] == "rotate" for e in events)


def test_rotate_no_audit_skips_log(isolated_store):
    from envchain.audit import read_events

    _seed(isolated_store)
    rotate_passphrase(PROFILE, OLD_PASS, NEW_PASS, audit=False)
    events = read_events(profile=PROFILE)
    assert not any(e["event"] == "rotate" for e in events)

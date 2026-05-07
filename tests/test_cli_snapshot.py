"""Tests for envchain.cli_snapshot."""

from __future__ import annotations

import argparse
import io

import pytest

from envchain.profile import Profile, save
from envchain.snapshot import save_snapshot
from envchain.cli_snapshot import (
    cmd_snapshot_delete,
    cmd_snapshot_list,
    cmd_snapshot_restore,
    cmd_snapshot_save,
)

PROFILE = "proj"
PASS = "Passw0rd!"
VARS = {"API_KEY": "abc123", "REGION": "us-east-1"}


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    return tmp_path


def _seed(isolated_store):
    p = Profile(name=PROFILE)
    for k, v in VARS.items():
        p.set_var(k, v)
    p.save(PASS)
    return p


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_snapshot_save_returns_zero(isolated_store, monkeypatch):
    _seed(isolated_store)
    monkeypatch.setattr("envchain.cli_snapshot._prompt_passphrase", lambda _: PASS)
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_snapshot_save(_args(profile=PROFILE, label="snap1"), out=out, err=err)
    assert rc == 0
    assert "snap1" in out.getvalue()


def test_cmd_snapshot_save_wrong_passphrase_returns_one(isolated_store, monkeypatch):
    _seed(isolated_store)
    monkeypatch.setattr("envchain.cli_snapshot._prompt_passphrase", lambda _: "wrong")
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_snapshot_save(_args(profile=PROFILE, label="snap1"), out=out, err=err)
    assert rc == 1
    assert "error" in err.getvalue()


def test_cmd_snapshot_list_empty(isolated_store):
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_snapshot_list(_args(profile=PROFILE), out=out, err=err)
    assert rc == 0
    assert "No snapshots" in out.getvalue()


def test_cmd_snapshot_list_shows_labels(isolated_store, monkeypatch):
    _seed(isolated_store)
    monkeypatch.setattr("envchain.cli_snapshot._prompt_passphrase", lambda _: PASS)
    cmd_snapshot_save(_args(profile=PROFILE, label="s1"), out=io.StringIO(), err=io.StringIO())
    cmd_snapshot_save(_args(profile=PROFILE, label="s2"), out=io.StringIO(), err=io.StringIO())
    out = io.StringIO()
    cmd_snapshot_list(_args(profile=PROFILE), out=out, err=io.StringIO())
    lines = out.getvalue().strip().splitlines()
    assert "s1" in lines and "s2" in lines


def test_cmd_snapshot_delete_returns_zero(isolated_store):
    save_snapshot(PROFILE, VARS, "to_del")
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_snapshot_delete(_args(profile=PROFILE, label="to_del"), out=out, err=err)
    assert rc == 0


def test_cmd_snapshot_delete_missing_returns_one(isolated_store):
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_snapshot_delete(_args(profile=PROFILE, label="ghost"), out=out, err=err)
    assert rc == 1
    assert "error" in err.getvalue()


def test_cmd_snapshot_restore_updates_profile(isolated_store, monkeypatch):
    _seed(isolated_store)
    monkeypatch.setattr("envchain.cli_snapshot._prompt_passphrase", lambda _: PASS)
    save_snapshot(PROFILE, {"API_KEY": "old_value"}, "rollback")
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_snapshot_restore(_args(profile=PROFILE, label="rollback"), out=out, err=err)
    assert rc == 0
    assert "restored" in out.getvalue()

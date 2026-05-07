"""Tests for envchain.cli_rename (cmd_rename)."""

from __future__ import annotations

import argparse
import pytest

from envchain import store, audit
from envchain.profile import Profile
from envchain.cli_rename import cmd_rename


PASS = "s3cr3t"


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_store_dir", lambda: tmp_path)
    monkeypatch.setattr(audit, "_log_path", lambda: tmp_path / "audit.log")
    return tmp_path


def _seed(name: str) -> None:
    p = Profile(name=name, vars={"X": "1"})
    p.save(PASS)


def _args(old: str, new: str) -> argparse.Namespace:
    return argparse.Namespace(old_name=old, new_name=new)


def test_cmd_rename_returns_zero_on_success(isolated_store, monkeypatch):
    _seed("proj")
    monkeypatch.setattr("getpass.getpass", lambda _: PASS)
    rc = cmd_rename(_args("proj", "project"))
    assert rc == 0
    assert "project" in store.list_profiles()
    assert "proj" not in store.list_profiles()


def test_cmd_rename_records_audit_event(isolated_store, monkeypatch):
    _seed("proj")
    monkeypatch.setattr("getpass.getpass", lambda _: PASS)
    cmd_rename(_args("proj", "project"))
    events = audit.read_events()
    assert any(e["action"] == "rename" and e["profile"] == "proj" for e in events)


def test_cmd_rename_missing_profile_returns_error(isolated_store, monkeypatch, capsys):
    monkeypatch.setattr("getpass.getpass", lambda _: PASS)
    rc = cmd_rename(_args("ghost", "new"))
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_cmd_rename_destination_exists_returns_error(isolated_store, monkeypatch, capsys):
    _seed("a")
    _seed("b")
    monkeypatch.setattr("getpass.getpass", lambda _: PASS)
    rc = cmd_rename(_args("a", "b"))
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_cmd_rename_wrong_passphrase_returns_error(isolated_store, monkeypatch, capsys):
    _seed("proj")
    monkeypatch.setattr("getpass.getpass", lambda _: "badpass")
    rc = cmd_rename(_args("proj", "other"))
    assert rc == 1


def test_cmd_rename_preserves_vars(isolated_store, monkeypatch):
    """Renamed profile should retain all original variables."""
    _seed("proj")
    monkeypatch.setattr("getpass.getpass", lambda _: PASS)
    cmd_rename(_args("proj", "project"))
    renamed = Profile.load("project", PASS)
    assert renamed.vars == {"X": "1"}

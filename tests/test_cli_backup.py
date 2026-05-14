"""Tests for envchain.cli_backup."""

from __future__ import annotations

import argparse
import pytest

from envchain.cli_backup import (
    cmd_backup_create,
    cmd_backup_restore,
    cmd_backup_list,
    cmd_backup_delete,
)
from envchain.store import save_profile as sp


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    store = tmp_path / "store"
    store.mkdir()
    backups = store / "backups"
    backups.mkdir()
    monkeypatch.setattr("envchain.store._store_dir", lambda: store)
    monkeypatch.setattr("envchain.backup._store_dir", lambda: store)
    monkeypatch.setattr("envchain.backup._backup_dir", lambda: backups)
    monkeypatch.setattr(
        "envchain.backup._backup_path",
        lambda label: backups / f"{label}.ecbak",
    )
    return store


def _seed(isolated_store):
    sp("proj", {"KEY": "val"}, "Secret1")


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"label": "snap1", "passphrase": "BackupPass1", "overwrite": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_backup_create_returns_zero(isolated_store):
    _seed(isolated_store)
    assert cmd_backup_create(_args()) == 0


def test_cmd_backup_create_no_profiles_returns_one(isolated_store):
    assert cmd_backup_create(_args()) == 1


def test_cmd_backup_create_duplicate_returns_one(isolated_store):
    _seed(isolated_store)
    cmd_backup_create(_args())
    assert cmd_backup_create(_args()) == 1


def test_cmd_backup_restore_returns_zero(isolated_store):
    _seed(isolated_store)
    cmd_backup_create(_args())
    # remove profile so restore has something to do
    (isolated_store / "proj.enc").unlink()
    assert cmd_backup_restore(_args()) == 0


def test_cmd_backup_restore_wrong_passphrase_returns_one(isolated_store):
    _seed(isolated_store)
    cmd_backup_create(_args())
    assert cmd_backup_restore(_args(passphrase="WrongPass9")) == 1


def test_cmd_backup_list_returns_zero(isolated_store, capsys):
    _seed(isolated_store)
    cmd_backup_create(_args())
    rc = cmd_backup_list(argparse.Namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "snap1" in out


def test_cmd_backup_list_empty_returns_zero(isolated_store, capsys):
    rc = cmd_backup_list(argparse.Namespace())
    assert rc == 0
    assert "No backups" in capsys.readouterr().out


def test_cmd_backup_delete_returns_zero(isolated_store):
    _seed(isolated_store)
    cmd_backup_create(_args())
    assert cmd_backup_delete(_args()) == 0


def test_cmd_backup_delete_missing_returns_one(isolated_store):
    assert cmd_backup_delete(_args(label="ghost")) == 1

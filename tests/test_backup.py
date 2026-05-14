"""Tests for envchain.backup."""

from __future__ import annotations

import pytest

from envchain.backup import (
    BackupError,
    create_backup,
    restore_backup,
    list_backups,
    delete_backup,
    _backup_path,
)
from envchain.profile import Profile, save as save_profile
from envchain.store import _store_dir


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path / "store")
    monkeypatch.setattr("envchain.backup._store_dir", lambda: tmp_path / "store")
    monkeypatch.setattr(
        "envchain.backup._backup_dir",
        lambda: tmp_path / "store" / "backups",
    )
    monkeypatch.setattr(
        "envchain.backup._backup_path",
        lambda label: tmp_path / "store" / "backups" / f"{label}.ecbak",
    )
    (tmp_path / "store").mkdir()
    return tmp_path / "store"


def _seed(store, passphrase="Secret1"):
    p = Profile(name="proj", vars={"KEY": "val"})
    from envchain.store import save_profile as sp
    sp("proj", p.as_env_dict(), passphrase)
    return p


def test_create_backup_returns_path(isolated_store):
    _seed(isolated_store)
    path = create_backup("snap1", "BackupPass1")
    assert path.exists()
    assert path.suffix == ".ecbak"


def test_create_backup_duplicate_label_raises(isolated_store):
    _seed(isolated_store)
    create_backup("snap1", "BackupPass1")
    with pytest.raises(BackupError, match="already exists"):
        create_backup("snap1", "BackupPass1")


def test_create_backup_no_profiles_raises(isolated_store):
    with pytest.raises(BackupError, match="No profiles"):
        create_backup("empty", "BackupPass1")


def test_restore_roundtrip(isolated_store):
    _seed(isolated_store)
    create_backup("snap1", "BackupPass1")

    # Remove the profile file so restore has something to do
    profile_file = isolated_store / "proj.enc"
    profile_file.unlink()

    restored = restore_backup("snap1", "BackupPass1")
    assert "proj" in restored
    assert profile_file.exists()


def test_restore_wrong_passphrase_raises(isolated_store):
    _seed(isolated_store)
    create_backup("snap1", "BackupPass1")
    with pytest.raises(BackupError, match="decrypt"):
        restore_backup("snap1", "WrongPass9")


def test_restore_missing_backup_raises(isolated_store):
    with pytest.raises(BackupError, match="not found"):
        restore_backup("ghost", "BackupPass1")


def test_restore_skips_existing_without_overwrite(isolated_store):
    _seed(isolated_store)
    create_backup("snap1", "BackupPass1")
    # Profile still exists — should be skipped
    restored = restore_backup("snap1", "BackupPass1", overwrite=False)
    assert restored == []


def test_restore_overwrites_when_flag_set(isolated_store):
    _seed(isolated_store)
    create_backup("snap1", "BackupPass1")
    restored = restore_backup("snap1", "BackupPass1", overwrite=True)
    assert "proj" in restored


def test_list_backups_returns_labels(isolated_store):
    _seed(isolated_store)
    create_backup("alpha", "BackupPass1")
    create_backup("beta", "BackupPass1")
    labels = list_backups()
    assert "alpha" in labels
    assert "beta" in labels


def test_delete_backup_removes_file(isolated_store):
    _seed(isolated_store)
    create_backup("snap1", "BackupPass1")
    delete_backup("snap1")
    assert list_backups() == []


def test_delete_missing_backup_raises(isolated_store):
    with pytest.raises(BackupError, match="not found"):
        delete_backup("ghost")

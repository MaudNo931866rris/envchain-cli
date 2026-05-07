"""Tests for envchain.snapshot."""

from __future__ import annotations

import os
import pytest

from envchain.snapshot import (
    Snapshot,
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


VARS = {"DB_URL": "postgres://localhost/dev", "SECRET": "hunter2"}
PROFILE = "myproject"


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    return tmp_path


def test_save_snapshot_returns_snapshot(isolated_store):
    snap = save_snapshot(PROFILE, VARS, "v1")
    assert isinstance(snap, Snapshot)
    assert snap.label == "v1"
    assert snap.profile == PROFILE
    assert snap.variables == VARS


def test_save_creates_file(isolated_store):
    save_snapshot(PROFILE, VARS, "v1")
    snap_dir = os.path.join(str(isolated_store), ".snapshots", PROFILE)
    assert os.path.isfile(os.path.join(snap_dir, "v1.json"))


def test_load_roundtrip(isolated_store):
    save_snapshot(PROFILE, VARS, "v1")
    snap = load_snapshot(PROFILE, "v1")
    assert snap.variables == VARS
    assert snap.label == "v1"


def test_save_duplicate_label_raises(isolated_store):
    save_snapshot(PROFILE, VARS, "v1")
    with pytest.raises(SnapshotError, match="already exists"):
        save_snapshot(PROFILE, VARS, "v1")


def test_load_missing_raises(isolated_store):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(PROFILE, "nonexistent")


def test_list_snapshots_empty(isolated_store):
    assert list_snapshots(PROFILE) == []


def test_list_snapshots_multiple(isolated_store):
    save_snapshot(PROFILE, VARS, "alpha")
    save_snapshot(PROFILE, VARS, "beta")
    save_snapshot(PROFILE, VARS, "gamma")
    assert list_snapshots(PROFILE) == ["alpha", "beta", "gamma"]


def test_delete_snapshot(isolated_store):
    save_snapshot(PROFILE, VARS, "v1")
    delete_snapshot(PROFILE, "v1")
    assert "v1" not in list_snapshots(PROFILE)


def test_delete_missing_raises(isolated_store):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(PROFILE, "ghost")


def test_snapshot_variables_are_independent_copy(isolated_store):
    original = dict(VARS)
    snap = save_snapshot(PROFILE, original, "v1")
    original["NEW_KEY"] = "should_not_appear"
    loaded = load_snapshot(PROFILE, "v1")
    assert "NEW_KEY" not in loaded.variables

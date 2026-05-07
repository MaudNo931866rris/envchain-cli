"""Tests for envchain.diff."""

from __future__ import annotations

import pytest

from envchain.diff import DiffError, ProfileDiff, VarDiff, diff_profiles
from envchain.profile import Profile, save


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_STORE_DIR", str(tmp_path))
    return tmp_path


PASS = "s3cret"


def _seed(name: str, vars_: dict, passphrase: str = PASS) -> None:
    p = Profile(name=name)
    for k, v in vars_.items():
        p.set_var(k, v)
    save(p, passphrase)


# ---------------------------------------------------------------------------
# diff_profiles – basic cases
# ---------------------------------------------------------------------------

def test_diff_added_key(isolated_store):
    _seed("left", {"A": "1"})
    _seed("right", {"A": "1", "B": "2"})
    result = diff_profiles("left", "right", PASS)
    assert result.has_differences()
    assert len(result.added) == 1
    assert result.added[0].key == "B"
    assert result.added[0].right_value == "2"


def test_diff_removed_key(isolated_store):
    _seed("left", {"A": "1", "B": "2"})
    _seed("right", {"A": "1"})
    result = diff_profiles("left", "right", PASS)
    assert len(result.removed) == 1
    assert result.removed[0].key == "B"
    assert result.removed[0].left_value == "2"


def test_diff_changed_key(isolated_store):
    _seed("left", {"A": "old"})
    _seed("right", {"A": "new"})
    result = diff_profiles("left", "right", PASS)
    assert len(result.changed) == 1
    entry = result.changed[0]
    assert entry.key == "A"
    assert entry.left_value == "old"
    assert entry.right_value == "new"


def test_diff_no_differences(isolated_store):
    _seed("left", {"A": "1", "B": "2"})
    _seed("right", {"A": "1", "B": "2"})
    result = diff_profiles("left", "right", PASS)
    assert not result.has_differences()
    assert result.unchanged == []


def test_diff_include_unchanged(isolated_store):
    _seed("left", {"A": "1"})
    _seed("right", {"A": "1"})
    result = diff_profiles("left", "right", PASS, include_unchanged=True)
    assert len(result.unchanged) == 1
    assert result.unchanged[0].key == "A"


def test_diff_entries_sorted_alphabetically(isolated_store):
    _seed("left", {"Z": "z", "A": "a", "M": "m"})
    _seed("right", {"Z": "z", "A": "x", "M": "m"})
    result = diff_profiles("left", "right", PASS, include_unchanged=True)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_diff_missing_profile_raises(isolated_store):
    _seed("exists", {"A": "1"})
    with pytest.raises(DiffError, match="ghost"):
        diff_profiles("exists", "ghost", PASS)


def test_var_diff_as_dict():
    vd = VarDiff("KEY", "changed", left_value="old", right_value="new")
    d = vd.as_dict()
    assert d["key"] == "KEY"
    assert d["status"] == "changed"
    assert d["left_value"] == "old"
    assert d["right_value"] == "new"

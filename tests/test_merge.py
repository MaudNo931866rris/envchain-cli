"""Tests for envchain.merge."""

from __future__ import annotations

import pytest

from envchain.profile import Profile, save
from envchain.merge import merge_profiles, MergeError


PASS = "TestPass1"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    return tmp_path


def _seed(name: str, vars_: dict, passphrase: str = PASS) -> None:
    p = Profile(name=name, passphrase=passphrase)
    for k, v in vars_.items():
        p.set_var(k, v)
    save(p)


# ---------------------------------------------------------------------------
# Basic merge behaviour
# ---------------------------------------------------------------------------

def test_merge_adds_keys_to_new_destination():
    _seed("src", {"FOO": "bar", "BAZ": "qux"})
    result = merge_profiles(["src"], "dst", PASS, PASS)
    assert set(result.merged_keys) == {"FOO", "BAZ"}
    assert result.skipped_keys == []
    assert result.overwritten_keys == []


def test_merge_preserves_vars_in_destination():
    from envchain.profile import load
    _seed("src", {"FOO": "from_src"})
    result = merge_profiles(["src"], "dst", PASS, PASS)
    assert result.merged_keys == ["FOO"]
    dst = load("dst", PASS)
    assert dst.as_env_dict()["FOO"] == "from_src"


def test_merge_skips_existing_key_without_overwrite():
    _seed("src", {"FOO": "new"})
    _seed("dst", {"FOO": "old"})
    result = merge_profiles(["src"], "dst", PASS, PASS, overwrite=False)
    assert "FOO" in result.skipped_keys
    assert result.merged_keys == []


def test_merge_overwrites_existing_key_when_flag_set():
    from envchain.profile import load
    _seed("src", {"FOO": "new"})
    _seed("dst", {"FOO": "old"})
    result = merge_profiles(["src"], "dst", PASS, PASS, overwrite=True)
    assert "FOO" in result.overwritten_keys
    dst = load("dst", PASS)
    assert dst.as_env_dict()["FOO"] == "new"


def test_merge_multiple_sources():
    _seed("src1", {"A": "1"})
    _seed("src2", {"B": "2"})
    result = merge_profiles(["src1", "src2"], "dst", PASS, PASS)
    assert set(result.merged_keys) == {"A", "B"}


# ---------------------------------------------------------------------------
# Error conditions
# ---------------------------------------------------------------------------

def test_merge_missing_source_raises():
    with pytest.raises(MergeError, match="does not exist"):
        merge_profiles(["ghost"], "dst", PASS, PASS)


def test_merge_empty_sources_raises():
    with pytest.raises(MergeError, match="At least one source"):
        merge_profiles([], "dst", PASS, PASS)


def test_merge_destination_in_sources_raises():
    _seed("profile", {"X": "1"})
    with pytest.raises(MergeError, match="must not appear in sources"):
        merge_profiles(["profile"], "profile", PASS, PASS)


def test_merge_result_as_dict():
    _seed("src", {"K": "v"})
    result = merge_profiles(["src"], "dst", PASS, PASS)
    d = result.as_dict()
    assert d["destination"] == "dst"
    assert "K" in d["merged_keys"]

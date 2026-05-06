"""Tests for envchain.copy (copy_var / move_var)."""

import os
import pytest

from envchain.copy import copy_var, move_var, CopyError
from envchain.profile import Profile, save, load, set_var
import envchain.store as store


PASS = "hunter2"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_store_dir", lambda: tmp_path)
    return tmp_path


def _seed(name: str, **vars) -> None:
    p = Profile(name=name)
    for k, v in vars.items():
        set_var(p, k, v)
    save(p, PASS)


# ---------------------------------------------------------------------------
# copy_var
# ---------------------------------------------------------------------------

def test_copy_var_creates_key_in_destination():
    _seed("src", API_KEY="abc123")
    copy_var("src", "API_KEY", "dst", "API_KEY", PASS)
    dst = load("dst", PASS)
    assert dst.as_env_dict()["API_KEY"] == "abc123"


def test_copy_var_can_rename_key():
    _seed("src", OLD_KEY="value")
    copy_var("src", "OLD_KEY", "dst", "NEW_KEY", PASS)
    dst = load("dst", PASS)
    assert "NEW_KEY" in dst.as_env_dict()
    assert "OLD_KEY" not in dst.as_env_dict()


def test_copy_var_source_key_missing_raises():
    _seed("src", FOO="bar")
    with pytest.raises(CopyError, match="'MISSING'"):
        copy_var("src", "MISSING", "dst", "MISSING", PASS)


def test_copy_var_no_overwrite_raises_if_key_exists():
    _seed("src", KEY="new_value")
    _seed("dst", KEY="old_value")
    with pytest.raises(CopyError, match="already exists"):
        copy_var("src", "KEY", "dst", "KEY", PASS, overwrite=False)


def test_copy_var_overwrite_replaces_existing_key():
    _seed("src", KEY="new_value")
    _seed("dst", KEY="old_value")
    copy_var("src", "KEY", "dst", "KEY", PASS, overwrite=True)
    dst = load("dst", PASS)
    assert dst.as_env_dict()["KEY"] == "new_value"


def test_copy_var_source_unchanged():
    _seed("src", API_KEY="secret")
    copy_var("src", "API_KEY", "dst", "API_KEY", PASS)
    src = load("src", PASS)
    assert src.as_env_dict()["API_KEY"] == "secret"


# ---------------------------------------------------------------------------
# move_var
# ---------------------------------------------------------------------------

def test_move_var_removes_key_from_source():
    _seed("src", TOKEN="tok")
    move_var("src", "TOKEN", "dst", "TOKEN", PASS)
    src = load("src", PASS)
    assert "TOKEN" not in src.as_env_dict()


def test_move_var_key_present_in_destination():
    _seed("src", TOKEN="tok")
    move_var("src", "TOKEN", "dst", "MOVED_TOKEN", PASS)
    dst = load("dst", PASS)
    assert dst.as_env_dict()["MOVED_TOKEN"] == "tok"


def test_move_var_missing_key_raises():
    _seed("src", FOO="bar")
    with pytest.raises(CopyError):
        move_var("src", "NOPE", "dst", "NOPE", PASS)

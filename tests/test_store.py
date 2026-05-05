"""Tests for envchain.store."""

import json
import os
import pytest

from envchain.store import (
    delete_profile,
    list_profiles,
    load_profile,
    save_profile,
)

PASS = "hunter2"
VARS = {"API_KEY": "abc123", "DEBUG": "true"}


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Redirect the profile store to a temp directory for every test."""
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_save_creates_file(isolated_store):
    save_profile("myproject", VARS, PASS)
    assert (isolated_store / "myproject.enc").exists()


def test_roundtrip(isolated_store):
    save_profile("myproject", VARS, PASS)
    result = load_profile("myproject", PASS)
    assert result == VARS


def test_load_wrong_passphrase(isolated_store):
    save_profile("myproject", VARS, PASS)
    with pytest.raises(Exception):
        load_profile("myproject", "wrongpass")


def test_load_missing_profile(isolated_store):
    with pytest.raises(FileNotFoundError, match="Profile 'ghost' not found"):
        load_profile("ghost", PASS)


def test_delete_profile(isolated_store):
    save_profile("myproject", VARS, PASS)
    delete_profile("myproject")
    assert not (isolated_store / "myproject.enc").exists()


def test_delete_missing_profile(isolated_store):
    with pytest.raises(FileNotFoundError):
        delete_profile("nonexistent")


def test_list_profiles_empty(isolated_store):
    assert list_profiles() == []


def test_list_profiles(isolated_store):
    for name in ("beta", "alpha", "gamma"):
        save_profile(name, VARS, PASS)
    assert list_profiles() == ["alpha", "beta", "gamma"]


def test_save_overwrites_existing(isolated_store):
    save_profile("myproject", VARS, PASS)
    new_vars = {"NEW": "value"}
    save_profile("myproject", new_vars, PASS)
    assert load_profile("myproject", PASS) == new_vars

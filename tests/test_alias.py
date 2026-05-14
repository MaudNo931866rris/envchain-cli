"""Unit tests for envchain.alias."""
from __future__ import annotations

import pytest

from envchain.alias import (
    AliasError,
    add_alias,
    aliases_for_profile,
    list_aliases,
    remove_alias,
    resolve_alias,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_add_alias_creates_entry():
    add_alias("prod", "myapp-production")
    assert resolve_alias("prod") == "myapp-production"


def test_add_alias_overwrites_existing():
    add_alias("prod", "myapp-production")
    add_alias("prod", "myapp-staging")
    assert resolve_alias("prod") == "myapp-staging"


def test_resolve_missing_alias_returns_none():
    assert resolve_alias("nonexistent") is None


def test_remove_alias_deletes_entry():
    add_alias("dev", "myapp-dev")
    remove_alias("dev")
    assert resolve_alias("dev") is None


def test_remove_missing_alias_raises():
    with pytest.raises(AliasError, match="not found"):
        remove_alias("ghost")


def test_list_aliases_returns_all():
    add_alias("a", "alpha")
    add_alias("b", "beta")
    result = list_aliases()
    assert result == {"a": "alpha", "b": "beta"}


def test_list_aliases_empty():
    assert list_aliases() == {}


def test_aliases_for_profile_finds_multiple():
    add_alias("x", "shared")
    add_alias("y", "shared")
    add_alias("z", "other")
    found = aliases_for_profile("shared")
    assert sorted(found) == ["x", "y"]


def test_aliases_for_profile_none_found():
    add_alias("x", "alpha")
    assert aliases_for_profile("beta") == []


def test_add_alias_empty_alias_raises():
    with pytest.raises(AliasError, match="empty"):
        add_alias("", "myprofile")


def test_add_alias_empty_profile_raises():
    with pytest.raises(AliasError, match="empty"):
        add_alias("myalias", "")

"""Tests for envchain.rename."""

from __future__ import annotations

import pytest

from envchain import store
from envchain.profile import Profile
from envchain.rename import RenameError, rename_profile


PASS = "s3cr3t"


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_store_dir", lambda: tmp_path)
    return tmp_path


def _seed(name: str, vars: dict[str, str] | None = None) -> None:
    p = Profile(name=name, vars=vars or {"KEY": "value"})
    p.save(PASS)


# ---------------------------------------------------------------------------
# rename_profile
# ---------------------------------------------------------------------------

def test_rename_moves_profile(isolated_store):
    _seed("alpha")
    rename_profile("alpha", "beta", PASS)
    assert "beta" in store.list_profiles()
    assert "alpha" not in store.list_profiles()


def test_rename_preserves_vars(isolated_store):
    _seed("alpha", {"FOO": "bar", "BAZ": "qux"})
    rename_profile("alpha", "beta", PASS)
    loaded = store.load_profile("beta", PASS)
    assert loaded == {"FOO": "bar", "BAZ": "qux"}


def test_rename_same_name_raises(isolated_store):
    _seed("alpha")
    with pytest.raises(RenameError, match="identical"):
        rename_profile("alpha", "alpha", PASS)


def test_rename_missing_source_raises(isolated_store):
    with pytest.raises(RenameError, match="does not exist"):
        rename_profile("ghost", "new", PASS)


def test_rename_destination_exists_raises(isolated_store):
    _seed("alpha")
    _seed("beta")
    with pytest.raises(RenameError, match="already exists"):
        rename_profile("alpha", "beta", PASS)


def test_rename_wrong_passphrase_raises(isolated_store):
    _seed("alpha")
    with pytest.raises(Exception):
        rename_profile("alpha", "beta", "wrongpass")
    # Original profile must still be intact
    assert "alpha" in store.list_profiles()

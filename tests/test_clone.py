"""Tests for envchain.clone."""

from __future__ import annotations

import os
import pytest

from envchain.clone import CloneError, clone_profile
from envchain.profile import load, save, Profile
from envchain.store import _store_dir


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path)
    monkeypatch.setattr("envchain.profile._store_dir", lambda: tmp_path)
    return tmp_path


def _seed(name: str, passphrase: str, vars: dict) -> Profile:
    p = Profile(name=name)
    for k, v in vars.items():
        p.set_var(k, v)
    save(p, passphrase)
    return p


class TestCloneProfile:
    def test_clone_creates_destination(self, isolated_store):
        _seed("src", "Pass1234", {"FOO": "bar"})
        clone_profile("src", "dst", "Pass1234")
        dst = load("dst", "Pass1234")
        assert dst.as_env_dict()["FOO"] == "bar"

    def test_clone_preserves_all_vars(self, isolated_store):
        _seed("src", "Pass1234", {"A": "1", "B": "2", "C": "3"})
        clone_profile("src", "dst", "Pass1234")
        dst = load("dst", "Pass1234")
        assert dst.as_env_dict() == {"A": "1", "B": "2", "C": "3"}

    def test_clone_with_different_dst_passphrase(self, isolated_store):
        _seed("src", "OldPass1", {"KEY": "value"})
        clone_profile("src", "dst", "OldPass1", dst_passphrase="NewPass2")
        dst = load("dst", "NewPass2")
        assert dst.as_env_dict()["KEY"] == "value"

    def test_clone_dst_not_readable_with_src_passphrase_when_different(self, isolated_store):
        _seed("src", "OldPass1", {"KEY": "value"})
        clone_profile("src", "dst", "OldPass1", dst_passphrase="NewPass2")
        with pytest.raises(Exception):
            load("dst", "OldPass1")

    def test_clone_same_name_raises(self, isolated_store):
        _seed("src", "Pass1234", {"X": "y"})
        with pytest.raises(CloneError, match="must differ"):
            clone_profile("src", "src", "Pass1234")

    def test_clone_existing_dst_raises_without_overwrite(self, isolated_store):
        _seed("src", "Pass1234", {"X": "1"})
        _seed("dst", "Pass1234", {"Y": "2"})
        with pytest.raises(CloneError, match="already exists"):
            clone_profile("src", "dst", "Pass1234")

    def test_clone_overwrite_replaces_destination(self, isolated_store):
        _seed("src", "Pass1234", {"NEW": "val"})
        _seed("dst", "Pass1234", {"OLD": "gone"})
        clone_profile("src", "dst", "Pass1234", overwrite=True)
        dst = load("dst", "Pass1234")
        assert "NEW" in dst.as_env_dict()
        assert "OLD" not in dst.as_env_dict()

    def test_clone_missing_source_raises(self, isolated_store):
        with pytest.raises(Exception):
            clone_profile("nonexistent", "dst", "Pass1234")

    def test_clone_returns_profile_object(self, isolated_store):
        _seed("src", "Pass1234", {"Z": "42"})
        result = clone_profile("src", "dst", "Pass1234")
        assert isinstance(result, Profile)
        assert result.name == "dst"

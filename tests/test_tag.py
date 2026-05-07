"""Tests for envchain.tag."""

from __future__ import annotations

import pytest

from envchain import tag as tag_mod
from envchain.tag import TagError


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(tag_mod, "_store_dir", lambda: tmp_path)
    yield tmp_path


def test_add_tag_creates_entry():
    tag_mod.add_tag("myproject", "production")
    assert "production" in tag_mod.get_tags("myproject")


def test_add_tag_idempotent():
    tag_mod.add_tag("myproject", "staging")
    tag_mod.add_tag("myproject", "staging")
    assert tag_mod.get_tags("myproject").count("staging") == 1


def test_add_multiple_tags():
    tag_mod.add_tag("proj", "alpha")
    tag_mod.add_tag("proj", "beta")
    tags = tag_mod.get_tags("proj")
    assert "alpha" in tags
    assert "beta" in tags


def test_remove_tag():
    tag_mod.add_tag("proj", "old")
    tag_mod.remove_tag("proj", "old")
    assert "old" not in tag_mod.get_tags("proj")


def test_remove_missing_tag_raises():
    with pytest.raises(TagError, match="not found"):
        tag_mod.remove_tag("proj", "ghost")


def test_get_tags_unknown_profile_returns_empty():
    assert tag_mod.get_tags("nonexistent") == []


def test_profiles_with_tag():
    tag_mod.add_tag("proj_a", "shared")
    tag_mod.add_tag("proj_b", "shared")
    tag_mod.add_tag("proj_c", "other")
    result = tag_mod.profiles_with_tag("shared")
    assert set(result) == {"proj_a", "proj_b"}


def test_profiles_with_tag_none_match():
    assert tag_mod.profiles_with_tag("unknown-tag") == []


def test_clear_tags_removes_all():
    tag_mod.add_tag("proj", "x")
    tag_mod.add_tag("proj", "y")
    tag_mod.clear_tags("proj")
    assert tag_mod.get_tags("proj") == []


def test_clear_tags_unknown_profile_no_error():
    tag_mod.clear_tags("never-existed")  # should not raise


def test_tags_persisted_across_calls():
    tag_mod.add_tag("persist", "saved")
    # re-read from disk by calling _load_tags directly
    data = tag_mod._load_tags()
    assert "saved" in data.get("persist", [])

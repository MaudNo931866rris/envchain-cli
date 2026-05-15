"""Tests for envchain.label module."""

from __future__ import annotations

import pytest

from envchain.label import (
    LabelError,
    find_by_label,
    get_label,
    list_labels,
    remove_label,
    set_label,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_set_and_get_label():
    set_label("myproject", "My Project", "Main dev profile")
    info = get_label("myproject")
    assert info is not None
    assert info["label"] == "My Project"
    assert info["description"] == "Main dev profile"


def test_get_missing_label_returns_none():
    assert get_label("nonexistent") is None


def test_set_label_empty_profile_raises():
    with pytest.raises(LabelError, match="Profile name"):
        set_label("", "Some Label")


def test_set_label_empty_label_raises():
    with pytest.raises(LabelError, match="Label must not be empty"):
        set_label("myproject", "")


def test_set_label_overwrites_existing():
    set_label("proj", "Old Label", "old desc")
    set_label("proj", "New Label", "new desc")
    info = get_label("proj")
    assert info["label"] == "New Label"
    assert info["description"] == "new desc"


def test_remove_label_deletes_entry():
    set_label("proj", "My Label")
    remove_label("proj")
    assert get_label("proj") is None


def test_remove_missing_label_raises():
    with pytest.raises(LabelError, match="No label found"):
        remove_label("ghost")


def test_list_labels_returns_all():
    set_label("alpha", "Alpha")
    set_label("beta", "Beta", "Beta desc")
    data = list_labels()
    assert "alpha" in data
    assert "beta" in data
    assert data["beta"]["description"] == "Beta desc"


def test_list_labels_empty():
    assert list_labels() == {}


def test_find_by_label_matches_label_text():
    set_label("proj1", "Production API", "")
    set_label("proj2", "Staging DB", "")
    results = find_by_label("production")
    assert len(results) == 1
    assert results[0]["profile"] == "proj1"


def test_find_by_label_matches_description():
    set_label("proj", "MyProj", "Handles billing service")
    results = find_by_label("billing")
    assert any(r["profile"] == "proj" for r in results)


def test_find_by_label_case_insensitive_default():
    set_label("proj", "FooBar")
    results = find_by_label("foobar")
    assert len(results) == 1


def test_find_by_label_case_sensitive_no_match():
    set_label("proj", "FooBar")
    results = find_by_label("foobar", case_sensitive=True)
    assert len(results) == 0


def test_find_by_label_no_results():
    set_label("proj", "Something")
    results = find_by_label("xyz_no_match")
    assert results == []

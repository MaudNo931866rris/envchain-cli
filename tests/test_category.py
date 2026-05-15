"""Tests for envchain.category."""

import pytest

from envchain.category import (
    CategoryError,
    find_by_category,
    get_category,
    list_categories,
    remove_category,
    set_category,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.category._store_dir", lambda: tmp_path)
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path)


def test_set_and_get_category():
    set_category("myproject", "work")
    assert get_category("myproject") == "work"


def test_get_missing_category_returns_none():
    assert get_category("nonexistent") is None


def test_set_category_empty_profile_raises():
    with pytest.raises(CategoryError, match="Profile"):
        set_category("", "work")


def test_set_category_empty_category_raises():
    with pytest.raises(CategoryError, match="Category"):
        set_category("myproject", "")


def test_set_category_blank_category_raises():
    with pytest.raises(CategoryError, match="blank"):
        set_category("myproject", "   ")


def test_set_category_overwrites_existing():
    set_category("myproject", "work")
    set_category("myproject", "personal")
    assert get_category("myproject") == "personal"


def test_remove_category_returns_true_when_exists():
    set_category("myproject", "work")
    assert remove_category("myproject") is True
    assert get_category("myproject") is None


def test_remove_category_returns_false_when_missing():
    assert remove_category("ghost") is False


def test_list_categories_sorted():
    set_category("zebra", "z-group")
    set_category("alpha", "a-group")
    set_category("middle", "m-group")
    result = list_categories()
    assert list(result.keys()) == ["alpha", "middle", "zebra"]


def test_list_categories_empty():
    assert list_categories() == {}


def test_find_by_category_returns_matching_profiles():
    set_category("proj-a", "work")
    set_category("proj-b", "personal")
    set_category("proj-c", "work")
    result = find_by_category("work")
    assert result == ["proj-a", "proj-c"]


def test_find_by_category_case_insensitive_default():
    set_category("proj-a", "Work")
    set_category("proj-b", "WORK")
    result = find_by_category("work")
    assert set(result) == {"proj-a", "proj-b"}


def test_find_by_category_case_sensitive_no_match():
    set_category("proj-a", "Work")
    result = find_by_category("work", case_sensitive=True)
    assert result == []


def test_find_by_category_no_match_returns_empty():
    set_category("proj-a", "work")
    assert find_by_category("unknown") == []

"""Tests for envchain.priority."""
from __future__ import annotations

import pytest

from envchain.priority import (
    PriorityError,
    clear_priority,
    get_priority,
    list_priorities,
    set_priority,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_set_and_get_priority():
    set_priority("prod", 10)
    assert get_priority("prod") == 10


def test_get_priority_returns_none_when_not_set():
    assert get_priority("nonexistent") is None


def test_set_priority_empty_profile_raises():
    with pytest.raises(PriorityError, match="empty"):
        set_priority("", 5)


def test_set_priority_non_integer_raises():
    with pytest.raises(PriorityError, match="integer"):
        set_priority("dev", "high")  # type: ignore[arg-type]


def test_set_priority_overwrites_existing():
    set_priority("staging", 3)
    set_priority("staging", 7)
    assert get_priority("staging") == 7


def test_clear_priority_removes_entry():
    set_priority("dev", 5)
    result = clear_priority("dev")
    assert result is True
    assert get_priority("dev") is None


def test_clear_priority_missing_returns_false():
    result = clear_priority("ghost")
    assert result is False


def test_list_priorities_sorted_by_level_descending():
    set_priority("low", 1)
    set_priority("high", 100)
    set_priority("mid", 50)
    entries = list_priorities()
    levels = [lvl for _, lvl in entries]
    assert levels == sorted(levels, reverse=True)


def test_list_priorities_same_level_sorted_by_name():
    set_priority("beta", 5)
    set_priority("alpha", 5)
    entries = list_priorities()
    names = [name for name, _ in entries]
    assert names == ["alpha", "beta"]


def test_list_priorities_empty():
    assert list_priorities() == []


def test_set_priority_returns_level():
    result = set_priority("ci", 42)
    assert result == 42


def test_negative_priority_allowed():
    set_priority("archive", -10)
    assert get_priority("archive") == -10

"""Integration tests: schedule interacts correctly with list/due across multiple profiles."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

import envchain.schedule as sched_mod
from envchain.schedule import (
    set_schedule,
    get_schedule,
    clear_schedule,
    list_schedules,
    due_schedules,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(sched_mod, "_store_dir", lambda: tmp_path)
    yield tmp_path


def test_multiple_profiles_independent():
    set_schedule("alpha", 7, action="rotate")
    set_schedule("beta", 30, action="expire")
    set_schedule("gamma", 1, action="remind")

    assert get_schedule("alpha")["action"] == "rotate"
    assert get_schedule("beta")["interval_days"] == 30
    assert get_schedule("gamma")["action"] == "remind"
    assert len(list_schedules()) == 3


def test_clear_one_does_not_affect_others():
    set_schedule("alpha", 7)
    set_schedule("beta", 7)
    clear_schedule("alpha")
    assert get_schedule("alpha") is None
    assert get_schedule("beta") is not None


def test_due_only_returns_past_next_run(monkeypatch):
    set_schedule("soon", 1)
    set_schedule("later", 90)

    # Advance time by 2 days — only 'soon' should be due
    future = datetime.utcnow() + timedelta(days=2)
    monkeypatch.setattr(sched_mod, "_now", lambda: future)

    due = due_schedules()
    due_names = [e["profile"] for e in due]
    assert "soon" in due_names
    assert "later" not in due_names


def test_list_schedules_sorted_alphabetically():
    set_schedule("zebra", 7)
    set_schedule("apple", 7)
    set_schedule("mango", 7)
    names = [e["profile"] for e in list_schedules()]
    assert names == sorted(names)


def test_schedule_entry_has_required_fields():
    set_schedule("proj", 14, action="expire")
    entry = get_schedule("proj")
    for field in ("action", "interval_days", "next_run", "created_at"):
        assert field in entry, f"Missing field: {field}"


def test_next_run_approximately_correct():
    now_before = datetime.utcnow()
    next_run = set_schedule("proj", 7)
    now_after = datetime.utcnow()
    expected_low = now_before + timedelta(days=7)
    expected_high = now_after + timedelta(days=7)
    assert expected_low <= next_run <= expected_high

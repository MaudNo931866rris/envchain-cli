"""Tests for envchain.schedule."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

import envchain.schedule as sched_mod
from envchain.schedule import (
    ScheduleError,
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


def test_set_schedule_returns_future_datetime():
    next_run = set_schedule("proj", 7)
    assert isinstance(next_run, datetime)
    assert next_run > datetime.utcnow()


def test_set_schedule_creates_entry():
    set_schedule("proj", 30, action="remind")
    entry = get_schedule("proj")
    assert entry is not None
    assert entry["action"] == "remind"
    assert entry["interval_days"] == 30


def test_get_schedule_returns_none_when_not_set():
    assert get_schedule("nonexistent") is None


def test_set_schedule_empty_profile_raises():
    with pytest.raises(ScheduleError, match="empty"):
        set_schedule("", 7)


def test_set_schedule_zero_interval_raises():
    with pytest.raises(ScheduleError, match="positive"):
        set_schedule("proj", 0)


def test_set_schedule_negative_interval_raises():
    with pytest.raises(ScheduleError, match="positive"):
        set_schedule("proj", -5)


def test_set_schedule_invalid_action_raises():
    with pytest.raises(ScheduleError, match="Unknown action"):
        set_schedule("proj", 7, action="delete")


def test_clear_schedule_returns_true_when_removed():
    set_schedule("proj", 14)
    assert clear_schedule("proj") is True
    assert get_schedule("proj") is None


def test_clear_schedule_returns_false_when_not_found():
    assert clear_schedule("ghost") is False


def test_list_schedules_returns_all():
    set_schedule("alpha", 7)
    set_schedule("beta", 14)
    entries = list_schedules()
    names = [e["profile"] for e in entries]
    assert "alpha" in names
    assert "beta" in names


def test_list_schedules_empty():
    assert list_schedules() == []


def test_due_schedules_returns_overdue(monkeypatch):
    set_schedule("proj", 1)
    # Wind clock forward so next_run is in the past
    future = datetime.utcnow() + timedelta(days=2)
    monkeypatch.setattr(sched_mod, "_now", lambda: future)
    due = due_schedules()
    assert any(e["profile"] == "proj" for e in due)


def test_due_schedules_empty_when_none_due():
    set_schedule("proj", 30)
    assert due_schedules() == []


def test_overwrite_schedule():
    set_schedule("proj", 7, action="rotate")
    set_schedule("proj", 14, action="remind")
    entry = get_schedule("proj")
    assert entry["interval_days"] == 14
    assert entry["action"] == "remind"

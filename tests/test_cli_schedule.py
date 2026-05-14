"""Tests for envchain.cli_schedule."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

import envchain.schedule as sched_mod
from envchain.cli_schedule import (
    cmd_schedule_set,
    cmd_schedule_clear,
    cmd_schedule_show,
    cmd_schedule_list,
    cmd_schedule_due,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(sched_mod, "_store_dir", lambda: tmp_path)
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "myproj", "interval_days": 7, "action": "rotate"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_schedule_set_returns_zero():
    assert cmd_schedule_set(_args()) == 0


def test_cmd_schedule_set_persists(capsys):
    cmd_schedule_set(_args(profile="ci", interval_days=14, action="remind"))
    entry = sched_mod.get_schedule("ci")
    assert entry["interval_days"] == 14
    assert entry["action"] == "remind"


def test_cmd_schedule_set_invalid_interval_returns_one():
    assert cmd_schedule_set(_args(interval_days=-1)) == 1


def test_cmd_schedule_clear_returns_zero():
    sched_mod.set_schedule("myproj", 7)
    assert cmd_schedule_clear(_args()) == 0


def test_cmd_schedule_clear_missing_returns_one():
    assert cmd_schedule_clear(_args(profile="ghost")) == 1


def test_cmd_schedule_show_returns_zero():
    sched_mod.set_schedule("myproj", 7)
    assert cmd_schedule_show(_args()) == 0


def test_cmd_schedule_show_not_set_returns_zero(capsys):
    rc = cmd_schedule_show(_args(profile="nope"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No schedule" in out


def test_cmd_schedule_list_returns_zero():
    sched_mod.set_schedule("alpha", 7)
    assert cmd_schedule_list(_args()) == 0


def test_cmd_schedule_list_empty_returns_zero(capsys):
    rc = cmd_schedule_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No schedules" in out


def test_cmd_schedule_due_returns_zero_none_due(capsys):
    sched_mod.set_schedule("myproj", 30)
    rc = cmd_schedule_due(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No schedules are currently due" in out


def test_cmd_schedule_due_lists_overdue(capsys, monkeypatch):
    sched_mod.set_schedule("myproj", 1)
    future = datetime.utcnow() + timedelta(days=2)
    monkeypatch.setattr(sched_mod, "_now", lambda: future)
    rc = cmd_schedule_due(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "myproj" in out

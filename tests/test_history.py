"""Tests for envchain.history and envchain.cli_history."""

from __future__ import annotations

import argparse
import pytest

from envchain.history import (
    HistoryEntry,
    HistoryError,
    clear_history,
    get_history,
    record_change,
)
from envchain.cli_history import cmd_history_show, cmd_history_clear


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


# --- history module ---

def test_record_change_returns_entry():
    entry = record_change("myproject", "API_KEY", None, "abc123", "set")
    assert isinstance(entry, HistoryEntry)
    assert entry.key == "API_KEY"
    assert entry.action == "set"
    assert entry.new_value == "abc123"
    assert entry.old_value is None


def test_record_change_persists():
    record_change("proj", "FOO", None, "bar", "set")
    record_change("proj", "FOO", "bar", "baz", "set")
    entries = get_history("proj")
    assert len(entries) == 2
    assert entries[0].new_value == "bar"
    assert entries[1].new_value == "baz"


def test_get_history_empty_profile():
    entries = get_history("nonexistent")
    assert entries == []


def test_filter_by_key():
    record_change("proj", "FOO", None, "1", "set")
    record_change("proj", "BAR", None, "2", "set")
    record_change("proj", "FOO", "1", "3", "set")
    entries = get_history("proj", key="FOO")
    assert all(e.key == "FOO" for e in entries)
    assert len(entries) == 2


def test_limit_caps_results():
    for i in range(5):
        record_change("proj", "X", str(i), str(i + 1), "set")
    entries = get_history("proj", limit=3)
    assert len(entries) == 3
    # limit returns the most recent
    assert entries[-1].new_value == "5"


def test_invalid_action_raises():
    with pytest.raises(HistoryError, match="Invalid action"):
        record_change("proj", "KEY", None, "val", "delete")


def test_clear_history_removes_file(isolated_store):
    record_change("proj", "KEY", None, "val", "set")
    clear_history("proj")
    assert get_history("proj") == []


def test_clear_history_noop_when_missing():
    clear_history("ghost")  # should not raise


def test_as_dict_shape():
    entry = record_change("proj", "K", "old", "new", "set")
    d = entry.as_dict()
    assert set(d.keys()) == {"key", "old_value", "new_value", "action", "timestamp"}


# --- CLI commands ---

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "proj", "key": None, "limit": None, "json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_history_show_returns_zero_with_entries():
    record_change("proj", "FOO", None, "bar", "set")
    assert cmd_history_show(_args()) == 0


def test_cmd_history_show_returns_zero_empty():
    assert cmd_history_show(_args(profile="empty")) == 0


def test_cmd_history_show_json_output(capsys):
    import json
    record_change("proj", "FOO", None, "bar", "set")
    rc = cmd_history_show(_args(json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["key"] == "FOO"


def test_cmd_history_clear_returns_zero():
    record_change("proj", "X", None, "1", "set")
    ns = argparse.Namespace(profile="proj")
    assert cmd_history_clear(ns) == 0
    assert get_history("proj") == []

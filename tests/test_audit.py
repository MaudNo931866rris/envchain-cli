"""Tests for envchain.audit and envchain.cli_audit."""

from __future__ import annotations

import os
import pytest

from envchain import audit
from envchain.cli_audit import cmd_audit_log, cmd_audit_clear


@pytest.fixture(autouse=True)
def isolated_audit(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path
    # cleanup handled by tmp_path


# --- audit module ---

def test_record_and_read_event():
    audit.record_event("load", "myproject")
    events = audit.read_events()
    assert len(events) == 1
    assert events[0]["action"] == "load"
    assert events[0]["profile"] == "myproject"


def test_record_with_detail():
    audit.record_event("set_var", "myproject", detail="API_KEY")
    events = audit.read_events()
    assert events[0]["detail"] == "API_KEY"


def test_filter_by_profile():
    audit.record_event("load", "alpha")
    audit.record_event("load", "beta")
    audit.record_event("delete", "alpha")

    alpha_events = audit.read_events(profile="alpha")
    assert len(alpha_events) == 2
    assert all(e["profile"] == "alpha" for e in alpha_events)


def test_read_events_empty_log():
    events = audit.read_events()
    assert events == []


def test_clear_log():
    audit.record_event("load", "myproject")
    audit.clear_log()
    assert audit.read_events() == []


def test_clear_nonexistent_log_is_safe():
    # Should not raise even when no log exists
    audit.clear_log()


# --- cli_audit commands ---

def test_cmd_audit_log_text(capsys):
    audit.record_event("load", "proj", detail="TOKEN")
    rc = cmd_audit_log(profile=None, output_format="text")
    assert rc == 0
    out = capsys.readouterr().out
    assert "load" in out
    assert "proj" in out


def test_cmd_audit_log_json(capsys):
    import json as _json
    audit.record_event("set_var", "proj")
    rc = cmd_audit_log(profile=None, output_format="json")
    assert rc == 0
    out = capsys.readouterr().out
    parsed = _json.loads(out)
    assert isinstance(parsed, list)
    assert parsed[0]["action"] == "set_var"


def test_cmd_audit_log_no_events_returns_1(capsys):
    rc = cmd_audit_log(profile="ghost")
    assert rc == 1


def test_cmd_audit_clear_requires_confirm(capsys):
    audit.record_event("load", "proj")
    rc = cmd_audit_clear(confirm=False)
    assert rc == 1
    assert audit.read_events()  # log still intact


def test_cmd_audit_clear_with_confirm(capsys):
    audit.record_event("load", "proj")
    rc = cmd_audit_clear(confirm=True)
    assert rc == 0
    assert audit.read_events() == []

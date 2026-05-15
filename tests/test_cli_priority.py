"""Tests for envchain.cli_priority."""
from __future__ import annotations

import argparse
import types

import pytest

from envchain.cli_priority import (
    cmd_priority_clear,
    cmd_priority_list,
    cmd_priority_set,
    cmd_priority_show,
)
from envchain.priority import set_priority


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_priority_set_returns_zero():
    assert cmd_priority_set(_args(profile="prod", level="10")) == 0


def test_cmd_priority_set_persists():
    cmd_priority_set(_args(profile="prod", level="10"))
    from envchain.priority import get_priority
    assert get_priority("prod") == 10


def test_cmd_priority_set_invalid_level_returns_one():
    assert cmd_priority_set(_args(profile="prod", level="high")) == 1


def test_cmd_priority_clear_returns_zero_when_set():
    set_priority("dev", 5)
    assert cmd_priority_clear(_args(profile="dev")) == 0


def test_cmd_priority_clear_returns_zero_when_not_set():
    assert cmd_priority_clear(_args(profile="ghost")) == 0


def test_cmd_priority_show_existing(capsys):
    set_priority("staging", 7)
    code = cmd_priority_show(_args(profile="staging"))
    assert code == 0
    assert "7" in capsys.readouterr().out


def test_cmd_priority_show_missing(capsys):
    code = cmd_priority_show(_args(profile="missing"))
    assert code == 0
    assert "No priority" in capsys.readouterr().out


def test_cmd_priority_list_empty(capsys):
    code = cmd_priority_list(_args())
    assert code == 0
    assert "No priorities" in capsys.readouterr().out


def test_cmd_priority_list_shows_entries(capsys):
    set_priority("a", 1)
    set_priority("b", 2)
    code = cmd_priority_list(_args())
    assert code == 0
    out = capsys.readouterr().out
    assert "a" in out
    assert "b" in out

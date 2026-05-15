"""Tests for envchain.cli_webhook."""
from __future__ import annotations

import argparse

import pytest

from envchain.cli_webhook import (
    cmd_webhook_list,
    cmd_webhook_remove,
    cmd_webhook_set,
    cmd_webhook_show,
)
from envchain.webhook import set_webhook


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "proj", "url": "https://example.com/hook", "events": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_webhook_set_returns_zero():
    assert cmd_webhook_set(_args()) == 0


def test_cmd_webhook_set_persists(capsys):
    cmd_webhook_set(_args(profile="myapp", url="https://hooks.example.com/"))
    from envchain.webhook import get_webhook
    cfg = get_webhook("myapp")
    assert cfg is not None
    assert cfg["url"] == "https://hooks.example.com/"


def test_cmd_webhook_set_with_events():
    rc = cmd_webhook_set(_args(events="set,delete"))
    assert rc == 0
    from envchain.webhook import get_webhook
    cfg = get_webhook("proj")
    assert cfg["events"] == ["set", "delete"]


def test_cmd_webhook_set_invalid_url_returns_one(capsys):
    rc = cmd_webhook_set(_args(url="not-a-url"))
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_cmd_webhook_remove_returns_zero():
    set_webhook("proj", "https://example.com/hook")
    rc = cmd_webhook_remove(_args())
    assert rc == 0


def test_cmd_webhook_remove_missing_returns_one(capsys):
    rc = cmd_webhook_remove(_args(profile="ghost"))
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_cmd_webhook_show_no_webhook(capsys):
    rc = cmd_webhook_show(_args(profile="nobody"))
    assert rc == 0
    captured = capsys.readouterr()
    assert "No webhook" in captured.out


def test_cmd_webhook_show_existing(capsys):
    set_webhook("proj", "https://example.com/hook", events=["set"])
    rc = cmd_webhook_show(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "https://example.com/hook" in captured.out
    assert "set" in captured.out


def test_cmd_webhook_list_empty(capsys):
    rc = cmd_webhook_list(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "No webhooks" in captured.out


def test_cmd_webhook_list_shows_entries(capsys):
    set_webhook("alpha", "https://alpha.example.com/")
    set_webhook("beta", "https://beta.example.com/")
    rc = cmd_webhook_list(_args())
    assert rc == 0
    captured = capsys.readouterr()
    assert "alpha" in captured.out
    assert "beta" in captured.out

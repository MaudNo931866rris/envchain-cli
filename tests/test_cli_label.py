"""Tests for envchain.cli_label module."""

from __future__ import annotations

import argparse

import pytest

from envchain.cli_label import (
    cmd_label_find,
    cmd_label_list,
    cmd_label_remove,
    cmd_label_set,
    cmd_label_show,
)
from envchain.label import set_label


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "proj", "label": "My Label", "description": "",
                "query": "label", "case_sensitive": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_label_set_returns_zero():
    assert cmd_label_set(_args()) == 0


def test_cmd_label_set_persists():
    cmd_label_set(_args(profile="proj", label="Cool Project", description="desc"))
    from envchain.label import get_label
    info = get_label("proj")
    assert info["label"] == "Cool Project"
    assert info["description"] == "desc"


def test_cmd_label_set_empty_label_returns_one():
    assert cmd_label_set(_args(label="")) == 1


def test_cmd_label_show_returns_zero_when_set():
    set_label("proj", "ShowMe", "a desc")
    assert cmd_label_show(_args(profile="proj")) == 0


def test_cmd_label_show_returns_zero_when_missing(capsys):
    rc = cmd_label_show(_args(profile="ghost"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No label" in out


def test_cmd_label_remove_returns_zero():
    set_label("proj", "To Remove")
    assert cmd_label_remove(_args(profile="proj")) == 0


def test_cmd_label_remove_missing_returns_one():
    assert cmd_label_remove(_args(profile="ghost")) == 1


def test_cmd_label_list_returns_zero(capsys):
    set_label("alpha", "Alpha")
    set_label("beta", "Beta")
    rc = cmd_label_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_label_list_empty_returns_zero(capsys):
    rc = cmd_label_list(_args())
    assert rc == 0
    assert "No labels" in capsys.readouterr().out


def test_cmd_label_find_returns_zero_on_match(capsys):
    set_label("proj", "Production API")
    rc = cmd_label_find(_args(query="production"))
    assert rc == 0
    assert "proj" in capsys.readouterr().out


def test_cmd_label_find_no_match_returns_zero(capsys):
    rc = cmd_label_find(_args(query="zzznomatch"))
    assert rc == 0
    assert "No matching" in capsys.readouterr().out

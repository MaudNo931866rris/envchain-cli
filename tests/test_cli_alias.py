"""Unit tests for envchain.cli_alias."""
from __future__ import annotations

import argparse

import pytest

from envchain.alias import add_alias, resolve_alias
from envchain.cli_alias import (
    cmd_alias_add,
    cmd_alias_list,
    cmd_alias_remove,
    cmd_alias_resolve,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_alias_add_returns_zero():
    rc = cmd_alias_add(_args(alias="prod", profile="myapp-prod"))
    assert rc == 0


def test_cmd_alias_add_persists():
    cmd_alias_add(_args(alias="prod", profile="myapp-prod"))
    assert resolve_alias("prod") == "myapp-prod"


def test_cmd_alias_add_empty_alias_returns_one():
    rc = cmd_alias_add(_args(alias="", profile="myapp-prod"))
    assert rc == 1


def test_cmd_alias_remove_returns_zero():
    add_alias("dev", "myapp-dev")
    rc = cmd_alias_remove(_args(alias="dev"))
    assert rc == 0


def test_cmd_alias_remove_missing_returns_one():
    rc = cmd_alias_remove(_args(alias="ghost"))
    assert rc == 1


def test_cmd_alias_resolve_prints_profile(capsys):
    add_alias("staging", "myapp-staging")
    rc = cmd_alias_resolve(_args(alias="staging"))
    assert rc == 0
    assert capsys.readouterr().out.strip() == "myapp-staging"


def test_cmd_alias_resolve_missing_returns_one():
    rc = cmd_alias_resolve(_args(alias="unknown"))
    assert rc == 1


def test_cmd_alias_list_returns_zero(capsys):
    add_alias("a", "alpha")
    rc = cmd_alias_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out


def test_cmd_alias_list_empty_prints_message(capsys):
    rc = cmd_alias_list(_args())
    assert rc == 0
    assert "No aliases" in capsys.readouterr().out

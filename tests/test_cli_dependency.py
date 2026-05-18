"""Tests for envchain.cli_dependency."""

from __future__ import annotations

import argparse

import pytest

from envchain.cli_dependency import (
    cmd_dep_add,
    cmd_dep_list,
    cmd_dep_remove,
    cmd_dep_resolve,
    cmd_dep_show_all,
)
from envchain.dependency import add_dependency


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.dependency._store_dir", lambda: tmp_path)
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_dep_add_returns_zero():
    rc = cmd_dep_add(_args(profile="app", depends_on="base"))
    assert rc == 0


def test_cmd_dep_add_persists():
    cmd_dep_add(_args(profile="app", depends_on="base"))
    from envchain.dependency import get_dependencies
    assert "base" in get_dependencies("app")


def test_cmd_dep_add_self_returns_one():
    rc = cmd_dep_add(_args(profile="app", depends_on="app"))
    assert rc == 1


def test_cmd_dep_remove_returns_zero():
    add_dependency("app", "base")
    rc = cmd_dep_remove(_args(profile="app", depends_on="base"))
    assert rc == 0


def test_cmd_dep_remove_missing_returns_one():
    rc = cmd_dep_remove(_args(profile="app", depends_on="ghost"))
    assert rc == 1


def test_cmd_dep_list_returns_zero(capsys):
    add_dependency("app", "base")
    rc = cmd_dep_list(_args(profile="app"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "base" in out


def test_cmd_dep_list_empty_profile(capsys):
    rc = cmd_dep_list(_args(profile="nothing"))
    assert rc == 0
    assert "no declared" in capsys.readouterr().out


def test_cmd_dep_resolve_returns_zero(capsys):
    add_dependency("app", "base")
    rc = cmd_dep_resolve(_args(profile="app"))
    assert rc == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[-1] == "app"


def test_cmd_dep_resolve_circular_returns_one():
    add_dependency("a", "b")
    add_dependency("b", "a")
    rc = cmd_dep_resolve(_args(profile="a"))
    assert rc == 1


def test_cmd_dep_show_all_empty(capsys):
    rc = cmd_dep_show_all(_args())
    assert rc == 0
    assert "No dependencies" in capsys.readouterr().out


def test_cmd_dep_show_all_populated(capsys):
    add_dependency("app", "base")
    rc = cmd_dep_show_all(_args())
    assert rc == 0
    assert "app" in capsys.readouterr().out

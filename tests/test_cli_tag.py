"""Tests for envchain.cli_tag."""

from __future__ import annotations

import argparse

import pytest

from envchain import tag as tag_mod
from envchain import cli_tag


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(tag_mod, "_store_dir", lambda: tmp_path)
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "myproject", "tag": "production"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_tag_add_returns_zero(capsys):
    rc = cli_tag.cmd_tag_add(_args())
    assert rc == 0
    assert "production" in capsys.readouterr().out


def test_cmd_tag_add_persists():
    cli_tag.cmd_tag_add(_args(profile="proj", tag="mytag"))
    assert "mytag" in tag_mod.get_tags("proj")


def test_cmd_tag_remove_returns_zero(capsys):
    tag_mod.add_tag("myproject", "production")
    rc = cli_tag.cmd_tag_remove(_args())
    assert rc == 0


def test_cmd_tag_remove_missing_returns_one(capsys):
    rc = cli_tag.cmd_tag_remove(_args(profile="proj", tag="ghost"))
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cmd_tag_list_shows_tags(capsys):
    tag_mod.add_tag("myproject", "production")
    tag_mod.add_tag("myproject", "eu-west")
    rc = cli_tag.cmd_tag_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "production" in out
    assert "eu-west" in out


def test_cmd_tag_list_empty(capsys):
    rc = cli_tag.cmd_tag_list(_args(profile="empty"))
    assert rc == 0
    assert "No tags" in capsys.readouterr().out


def test_cmd_tag_find_returns_profiles(capsys):
    tag_mod.add_tag("proj_a", "shared")
    tag_mod.add_tag("proj_b", "shared")
    rc = cli_tag.cmd_tag_find(_args(tag="shared"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "proj_a" in out
    assert "proj_b" in out


def test_cmd_tag_find_no_results(capsys):
    rc = cli_tag.cmd_tag_find(_args(tag="none"))
    assert rc == 0
    assert "No profiles" in capsys.readouterr().out

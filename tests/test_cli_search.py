"""Tests for envchain.cli_search."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from envchain.cli_search import cmd_search
from envchain.profile import Profile, save


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.store._store_dir", lambda: tmp_path)
    monkeypatch.setattr("envchain.profile._store_dir", lambda: tmp_path, raising=False)
    monkeypatch.setattr("envchain.search.load", __import__("envchain.profile", fromlist=["load"]).load)
    return tmp_path


PASS = "s3cr3t"


def _seed(name, vars_dict):
    p = Profile(name)
    for k, v in vars_dict.items():
        p.set_var(k, v)
    save(p, PASS)


def _args(**kwargs):
    defaults = dict(query="", values=False, show=False, case_sensitive=False, profiles="")
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_cmd_search_returns_zero_on_match(isolated_store, capsys):
    _seed("myapp", {"DB_HOST": "localhost"})
    with patch("envchain.cli_search.list_profiles", return_value=["myapp"]), \
         patch("envchain.cli_search.getpass.getpass", return_value=PASS):
        rc = cmd_search(_args(query="DB_HOST"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "myapp" in out


def test_cmd_search_returns_zero_no_match(isolated_store, capsys):
    _seed("myapp", {"DB_HOST": "localhost"})
    with patch("envchain.cli_search.list_profiles", return_value=["myapp"]), \
         patch("envchain.cli_search.getpass.getpass", return_value=PASS):
        rc = cmd_search(_args(query="NONEXISTENT"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No matches" in out


def test_cmd_search_no_profiles_returns_error(isolated_store, capsys):
    with patch("envchain.cli_search.list_profiles", return_value=[]):
        rc = cmd_search(_args(query="anything"))
    assert rc == 1
    err = capsys.readouterr().err
    assert "No profiles" in err


def test_cmd_search_explicit_profiles(isolated_store, capsys):
    _seed("alpha", {"ALPHA_KEY": "v"})
    _seed("beta", {"BETA_KEY": "v"})
    with patch("envchain.cli_search.getpass.getpass", return_value=PASS):
        rc = cmd_search(_args(query="ALPHA_KEY", profiles="alpha"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "ALPHA_KEY" in out
    assert "BETA_KEY" not in out


def test_cmd_search_show_values(isolated_store, capsys):
    _seed("proj", {"MY_VAR": "my_secret_value"})
    with patch("envchain.cli_search.list_profiles", return_value=["proj"]), \
         patch("envchain.cli_search.getpass.getpass", return_value=PASS):
        rc = cmd_search(_args(query="MY_VAR", show=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "my_secret_value" in out

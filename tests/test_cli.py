"""Tests for envchain.cli command handlers."""

import os
import pytest
from unittest.mock import patch, MagicMock

import envchain.cli as cli
import envchain.profile as prof
from envchain import store


PASSPHRASE = "test-passphrase"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_store_dir", lambda: tmp_path)
    yield tmp_path


def _make_profile(name: str, variables: dict) -> None:
    p = prof.load(name, PASSPHRASE)
    for k, v in variables.items():
        prof.set_var(p, k, v)
    prof.save(p, PASSPHRASE)


# ---------------------------------------------------------------------------
# cmd_set
# ---------------------------------------------------------------------------

def test_cmd_set_creates_and_saves_vars():
    args = MagicMock(profile="myproject", var=["FOO=bar", "BAZ=qux"])
    with patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_set(args)
    assert rc == 0
    p = prof.load("myproject", PASSPHRASE)
    assert prof.as_env_dict(p)["FOO"] == "bar"
    assert prof.as_env_dict(p)["BAZ"] == "qux"


def test_cmd_set_invalid_format_returns_error():
    args = MagicMock(profile="myproject", var=["INVALID"])
    with patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_set(args)
    assert rc == 1


# ---------------------------------------------------------------------------
# cmd_unset
# ---------------------------------------------------------------------------

def test_cmd_unset_removes_key():
    _make_profile("proj", {"KEY": "value", "OTHER": "keep"})
    args = MagicMock(profile="proj", key=["KEY"])
    with patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_unset(args)
    assert rc == 0
    p = prof.load("proj", PASSPHRASE)
    assert "KEY" not in prof.as_env_dict(p)
    assert prof.as_env_dict(p)["OTHER"] == "keep"


def test_cmd_unset_missing_key_warns_but_succeeds():
    _make_profile("proj", {"KEY": "value"})
    args = MagicMock(profile="proj", key=["MISSING"])
    with patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_unset(args)
    assert rc == 0


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

def test_cmd_list_prints_keys(capsys):
    _make_profile("proj", {"ALPHA": "1", "BETA": "2"})
    args = MagicMock(profile="proj")
    with patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_list(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "ALPHA" in captured.out
    assert "BETA" in captured.out
    assert "1" not in captured.out  # values must not be shown


def test_cmd_list_empty_profile(capsys):
    args = MagicMock(profile="empty")
    with patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_list(args)
    assert rc == 0
    assert "empty" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# cmd_delete
# ---------------------------------------------------------------------------

def test_cmd_delete_confirmed(capsys):
    _make_profile("todelete", {"X": "y"})
    args = MagicMock(profile="todelete")
    with patch("builtins.input", return_value="y"), \
         patch("getpass.getpass", return_value=PASSPHRASE):
        rc = cli.cmd_delete(args)
    assert rc == 0


def test_cmd_delete_aborted(capsys):
    _make_profile("todelete", {"X": "y"})
    args = MagicMock(profile="todelete")
    with patch("builtins.input", return_value="n"):
        rc = cli.cmd_delete(args)
    assert rc == 0
    # profile should still exist
    p = prof.load("todelete", PASSPHRASE)
    assert prof.as_env_dict(p)["X"] == "y"


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_build_parser_set_subcommand():
    parser = cli.build_parser()
    args = parser.parse_args(["set", "myprofile", "FOO=bar"])
    assert args.command == "set"
    assert args.profile == "myprofile"
    assert args.var == ["FOO=bar"]


def test_build_parser_run_subcommand():
    parser = cli.build_parser()
    args = parser.parse_args(["run", "myprofile", "env", "-u", "HOME"])
    assert args.command == "run"
    assert args.command_name if hasattr(args, "command_name") else True
    assert "env" in args.command

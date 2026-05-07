"""Tests for envchain.cli_template."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pytest

from envchain.cli_template import cmd_template_render
from envchain.profile import Profile, save


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_STORE_DIR", str(tmp_path))
    return tmp_path


def _seed(name: str, passphrase: str, variables: dict) -> None:
    p = Profile(name=name)
    for k, v in variables.items():
        p.set_var(k, v)
    save(p, passphrase)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "profile": "proj",
        "template_file": "-",
        "output": "-",
        "loose": False,
        "passphrase": "Secret1!",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_render_returns_zero_on_success(isolated_store, capsys):
    _seed("proj", "Secret1!", {"APP": "envchain"})
    args = _args()
    # Patch stdin
    import envchain.cli_template as mod
    orig = sys.stdin
    sys.stdin = io.StringIO("name=${APP}")
    try:
        rc = cmd_template_render(args)
    finally:
        sys.stdin = orig
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == "name=envchain"


def test_cmd_render_missing_template_file_returns_one(isolated_store):
    _seed("proj", "Secret1!", {})
    args = _args(template_file="/nonexistent/template.txt")
    rc = cmd_template_render(args)
    assert rc == 1


def test_cmd_render_strict_missing_var_returns_one(isolated_store, capsys):
    _seed("proj", "Secret1!", {"FOO": "bar"})
    import envchain.cli_template as mod
    orig = sys.stdin
    sys.stdin = io.StringIO("${FOO} ${NOPE}")
    try:
        rc = cmd_template_render(args=_args(loose=False))
    finally:
        sys.stdin = orig
    assert rc == 1


def test_cmd_render_writes_to_file(isolated_store, tmp_path):
    _seed("proj", "Secret1!", {"X": "42"})
    out_file = tmp_path / "out.txt"
    args = _args(output=str(out_file))
    import sys, io
    orig = sys.stdin
    sys.stdin = io.StringIO("value=$X")
    try:
        rc = cmd_template_render(args)
    finally:
        sys.stdin = orig
    assert rc == 0
    assert out_file.read_text() == "value=42"


def test_cmd_render_wrong_passphrase_returns_one(isolated_store, capsys):
    _seed("proj", "Secret1!", {"K": "v"})
    import sys, io
    orig = sys.stdin
    sys.stdin = io.StringIO("$K")
    try:
        rc = cmd_template_render(args=_args(passphrase="WrongPass9!"))
    finally:
        sys.stdin = orig
    assert rc == 1

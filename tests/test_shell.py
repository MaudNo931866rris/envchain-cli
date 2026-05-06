"""Tests for envchain.shell — shell export emission."""

from __future__ import annotations

import os
import pytest

from envchain.shell import emit_shell_exports, ShellError, SUPPORTED_SHELLS
from envchain.profile import Profile, save


PASSPHRASE = "shell-test-secret"


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_STORE_DIR", str(tmp_path))
    return tmp_path


def _seed(name: str, vars: dict[str, str]) -> None:
    p = Profile(name)
    for k, v in vars.items():
        p.set_var(k, v)
    save(p, PASSPHRASE)


# ---------------------------------------------------------------------------
# emit_shell_exports — posix / bash / zsh
# ---------------------------------------------------------------------------

def test_posix_export_format(isolated_store):
    _seed("myapp", {"API_KEY": "abc123", "DEBUG": "true"})
    output = emit_shell_exports("myapp", PASSPHRASE, shell="posix")
    assert "export API_KEY=" in output
    assert "export DEBUG=" in output


def test_bash_same_as_posix(isolated_store):
    _seed("myapp", {"TOKEN": "xyz"})
    posix = emit_shell_exports("myapp", PASSPHRASE, shell="posix")
    bash = emit_shell_exports("myapp", PASSPHRASE, shell="bash")
    assert posix == bash


def test_zsh_same_as_posix(isolated_store):
    _seed("myapp", {"TOKEN": "xyz"})
    posix = emit_shell_exports("myapp", PASSPHRASE, shell="posix")
    zsh = emit_shell_exports("myapp", PASSPHRASE, shell="zsh")
    assert posix == zsh


def test_values_are_quoted(isolated_store):
    _seed("myapp", {"PATH_VAR": "/usr/local/bin:/usr/bin"})
    output = emit_shell_exports("myapp", PASSPHRASE, shell="posix")
    # shlex.quote wraps values with spaces/colons in single quotes
    assert "'/usr/local/bin:/usr/bin'" in output


# ---------------------------------------------------------------------------
# emit_shell_exports — fish
# ---------------------------------------------------------------------------

def test_fish_export_format(isolated_store):
    _seed("myapp", {"API_KEY": "abc123"})
    output = emit_shell_exports("myapp", PASSPHRASE, shell="fish")
    assert "set -gx API_KEY" in output
    assert "export" not in output


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_profile_returns_comment(isolated_store):
    _seed("empty", {})
    output = emit_shell_exports("empty", PASSPHRASE, shell="posix")
    assert output.startswith("# envchain:")


def test_unsupported_shell_raises(isolated_store):
    _seed("myapp", {"X": "1"})
    with pytest.raises(ShellError, match="Unsupported shell"):
        emit_shell_exports("myapp", PASSPHRASE, shell="powershell")  # type: ignore[arg-type]


def test_wrong_passphrase_propagates(isolated_store):
    _seed("myapp", {"X": "1"})
    with pytest.raises(Exception):
        emit_shell_exports("myapp", "wrong-passphrase", shell="posix")


def test_output_is_sorted(isolated_store):
    _seed("myapp", {"ZEBRA": "z", "ALPHA": "a", "MIDDLE": "m"})
    output = emit_shell_exports("myapp", PASSPHRASE, shell="posix")
    lines = [l for l in output.splitlines() if l.strip()]
    keys = [line.split("=")[0].replace("export ", "") for line in lines]
    assert keys == sorted(keys)

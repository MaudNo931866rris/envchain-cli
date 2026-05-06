"""Shell completion and environment variable export helpers."""

from __future__ import annotations

import shlex
from typing import Literal

from envchain.profile import load

ShellType = Literal["bash", "zsh", "fish", "posix"]

SUPPORTED_SHELLS: tuple[ShellType, ...] = ("bash", "zsh", "fish", "posix")


class ShellError(Exception):
    """Raised when shell emission fails."""


def _export_posix(env: dict[str, str]) -> str:
    """Emit POSIX-compatible export statements."""
    lines = []
    for key, value in sorted(env.items()):
        quoted = shlex.quote(value)
        lines.append(f"export {key}={quoted}")
    return "\n".join(lines)


def _export_fish(env: dict[str, str]) -> str:
    """Emit fish shell set statements."""
    lines = []
    for key, value in sorted(env.items()):
        quoted = shlex.quote(value)
        lines.append(f"set -gx {key} {quoted}")
    return "\n".join(lines)


def emit_shell_exports(
    profile_name: str,
    passphrase: str,
    shell: ShellType = "posix",
) -> str:
    """Return a string of shell export statements for the given profile.

    Args:
        profile_name: Name of the envchain profile to load.
        passphrase: Decryption passphrase for the profile.
        shell: Target shell syntax (bash/zsh share posix syntax).

    Returns:
        A multi-line string ready to be eval'd in the target shell.

    Raises:
        ShellError: If the shell type is unsupported.
        KeyError / FileNotFoundError: Propagated from the profile loader.
    """
    if shell not in SUPPORTED_SHELLS:
        raise ShellError(
            f"Unsupported shell '{shell}'. Choose from: {', '.join(SUPPORTED_SHELLS)}"
        )

    profile = load(profile_name, passphrase)
    env = profile.as_env_dict()

    if not env:
        return "# envchain: no variables defined in profile '{}'".format(profile_name)

    if shell == "fish":
        return _export_fish(env)
    return _export_posix(env)

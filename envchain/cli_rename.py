"""CLI command for renaming a profile."""

from __future__ import annotations

import argparse
import getpass
import sys

from envchain.rename import RenameError, rename_profile
from envchain import audit


def _prompt_passphrase(profile_name: str) -> str:
    """Prompt the user for the passphrase of *profile_name*.

    Reads from the terminal without echoing the input.
    Returns the entered passphrase string.
    """
    return getpass.getpass(f"Passphrase for '{profile_name}': ")


def cmd_rename(args: argparse.Namespace) -> int:
    """Handle the ``envchain rename <old> <new>`` command.

    Returns 0 on success, 1 on failure.
    """
    old_name: str = args.old_name
    new_name: str = args.new_name

    passphrase = _prompt_passphrase(old_name)

    try:
        rename_profile(old_name, new_name, passphrase)
    except RenameError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Wrong passphrase or decryption failure
        print(f"error: {exc}", file=sys.stderr)
        return 1

    audit.record_event(
        action="rename",
        profile=old_name,
        detail=f"renamed to '{new_name}'",
    )

    print(f"Profile '{old_name}' renamed to '{new_name}'.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *rename* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "rename",
        help="Rename a profile.",
        description="Rename an existing profile to a new name.",
    )
    p.add_argument("old_name", metavar="OLD", help="Current profile name.")
    p.add_argument("new_name", metavar="NEW", help="New profile name.")
    p.set_defaults(func=cmd_rename)

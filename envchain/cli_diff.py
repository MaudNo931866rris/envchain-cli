"""CLI commands for diffing two envchain profiles."""

from __future__ import annotations

import argparse
import getpass
import sys

from envchain.diff import DiffError, diff_profiles

# Status symbols and colours (no external deps)
_SYMBOLS = {
    "added":     ("+", "\033[32m"),   # green
    "removed":   ("-", "\033[31m"),   # red
    "changed":   ("~", "\033[33m"),   # yellow
    "unchanged": (" ", "\033[0m"),
}
_RESET = "\033[0m"


def _render(diff, *, colour: bool, show_values: bool) -> str:
    lines = [
        f"Diff: {diff.left_profile}  →  {diff.right_profile}",
        "-" * 48,
    ]
    if not diff.entries:
        lines.append("(no differences)")
        return "\n".join(lines)

    for entry in diff.entries:
        sym, clr = _SYMBOLS[entry.status]
        prefix = f"{clr}{sym}{_RESET}" if colour else sym
        if show_values and entry.status == "changed":
            lines.append(f"  {prefix} {entry.key}")
            lines.append(f"      < {entry.left_value}")
            lines.append(f"      > {entry.right_value}")
        elif show_values and entry.status == "added":
            lines.append(f"  {prefix} {entry.key} = {entry.right_value}")
        elif show_values and entry.status == "removed":
            lines.append(f"  {prefix} {entry.key} = {entry.left_value}")
        else:
            lines.append(f"  {prefix} {entry.key}")
    return "\n".join(lines)


def cmd_diff(args: argparse.Namespace) -> int:
    passphrase = getpass.getpass("Passphrase: ")
    try:
        result = diff_profiles(
            args.left,
            args.right,
            passphrase,
            include_unchanged=getattr(args, "unchanged", False),
        )
    except DiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    colour = sys.stdout.isatty() and not getattr(args, "no_color", False)
    show_values = getattr(args, "values", False)
    print(_render(result, colour=colour, show_values=show_values))
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Compare variables between two profiles")
    p.add_argument("left", help="Base profile name")
    p.add_argument("right", help="Profile to compare against")
    p.add_argument(
        "--values", action="store_true", help="Show variable values in output"
    )
    p.add_argument(
        "--unchanged", action="store_true", help="Also show unchanged keys"
    )
    p.add_argument(
        "--no-color", dest="no_color", action="store_true", help="Disable colour output"
    )
    p.set_defaults(func=cmd_diff)

"""CLI commands for variable history inspection."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from envchain.history import HistoryError, clear_history, get_history


def cmd_history_show(args: argparse.Namespace) -> int:
    """Print the change history for a profile, optionally filtered by key."""
    try:
        entries = get_history(
            profile=args.profile,
            key=getattr(args, "key", None) or None,
            limit=getattr(args, "limit", None),
        )
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print("No history found.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps([e.as_dict() for e in entries], indent=2))
        return 0

    for entry in entries:
        old = entry.old_value if entry.old_value is not None else "<unset>"
        new = entry.new_value if entry.new_value is not None else "<unset>"
        print(f"[{entry.timestamp}] {entry.action.upper():6s} {entry.key}: {old} -> {new}")

    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    """Clear the history log for a profile."""
    try:
        clear_history(args.profile)
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"History cleared for profile '{args.profile}'.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # history show
    p_show = subparsers.add_parser("history", help="Show variable change history")
    p_show.add_argument("profile", help="Profile name")
    p_show.add_argument("--key", default=None, help="Filter by variable key")
    p_show.add_argument("--limit", type=int, default=None, help="Max entries to show")
    p_show.add_argument("--json", action="store_true", help="Output as JSON")
    p_show.set_defaults(func=cmd_history_show)

    # history clear
    p_clear = subparsers.add_parser("history-clear", help="Clear variable change history")
    p_clear.add_argument("profile", help="Profile name")
    p_clear.set_defaults(func=cmd_history_clear)

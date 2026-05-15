"""CLI commands for profile priority management."""
from __future__ import annotations

import argparse
import sys

from envchain.priority import (
    PriorityError,
    clear_priority,
    get_priority,
    list_priorities,
    set_priority,
)


def cmd_priority_set(args: argparse.Namespace) -> int:
    try:
        level = int(args.level)
    except ValueError:
        print(f"error: level must be an integer, got {args.level!r}", file=sys.stderr)
        return 1
    try:
        set_priority(args.profile, level)
        print(f"Priority for '{args.profile}' set to {level}.")
        return 0
    except PriorityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_priority_clear(args: argparse.Namespace) -> int:
    removed = clear_priority(args.profile)
    if removed:
        print(f"Priority for '{args.profile}' cleared.")
    else:
        print(f"No priority set for '{args.profile}'.")
    return 0


def cmd_priority_show(args: argparse.Namespace) -> int:
    level = get_priority(args.profile)
    if level is None:
        print(f"No priority set for '{args.profile}'.")
    else:
        print(f"{args.profile}: {level}")
    return 0


def cmd_priority_list(_args: argparse.Namespace) -> int:
    entries = list_priorities()
    if not entries:
        print("No priorities set.")
        return 0
    for profile, level in entries:
        print(f"{profile}: {level}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("priority", help="Manage profile priorities")
    sub = p.add_subparsers(dest="priority_cmd", required=True)

    ps = sub.add_parser("set", help="Set priority for a profile")
    ps.add_argument("profile")
    ps.add_argument("level", help="Integer priority level")
    ps.set_defaults(func=cmd_priority_set)

    pc = sub.add_parser("clear", help="Clear priority for a profile")
    pc.add_argument("profile")
    pc.set_defaults(func=cmd_priority_clear)

    psh = sub.add_parser("show", help="Show priority for a profile")
    psh.add_argument("profile")
    psh.set_defaults(func=cmd_priority_show)

    pl = sub.add_parser("list", help="List all priorities")
    pl.set_defaults(func=cmd_priority_list)

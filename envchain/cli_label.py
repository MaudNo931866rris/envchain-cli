"""CLI commands for managing profile labels and descriptions."""

from __future__ import annotations

import argparse
import sys

from envchain.label import (
    LabelError,
    find_by_label,
    get_label,
    list_labels,
    remove_label,
    set_label,
)


def cmd_label_set(args: argparse.Namespace) -> int:
    """Set a label (and optional description) on a profile."""
    try:
        set_label(args.profile, args.label, args.description or "")
        print(f"Label set for profile '{args.profile}'.")
        return 0
    except LabelError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_label_remove(args: argparse.Namespace) -> int:
    """Remove the label from a profile."""
    try:
        remove_label(args.profile)
        print(f"Label removed from profile '{args.profile}'.")
        return 0
    except LabelError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_label_show(args: argparse.Namespace) -> int:
    """Show the label for a specific profile."""
    info = get_label(args.profile)
    if info is None:
        print(f"No label set for profile '{args.profile}'.")
        return 0
    print(f"Label      : {info['label']}")
    if info.get("description"):
        print(f"Description: {info['description']}")
    return 0


def cmd_label_list(args: argparse.Namespace) -> int:
    """List all profiles that have labels."""
    data = list_labels()
    if not data:
        print("No labels defined.")
        return 0
    for profile, info in sorted(data.items()):
        desc = f"  — {info['description']}" if info.get("description") else ""
        print(f"{profile}: {info['label']}{desc}")
    return 0


def cmd_label_find(args: argparse.Namespace) -> int:
    """Search profiles by label or description."""
    results = find_by_label(args.query, case_sensitive=args.case_sensitive)
    if not results:
        print("No matching profiles found.")
        return 0
    for item in results:
        desc = f"  — {item['description']}" if item.get("description") else ""
        print(f"{item['profile']}: {item['label']}{desc}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p_set = subparsers.add_parser("label-set", help="Set a label for a profile")
    p_set.add_argument("profile")
    p_set.add_argument("label")
    p_set.add_argument("--description", default="")
    p_set.set_defaults(func=cmd_label_set)

    p_rm = subparsers.add_parser("label-remove", help="Remove a profile label")
    p_rm.add_argument("profile")
    p_rm.set_defaults(func=cmd_label_remove)

    p_show = subparsers.add_parser("label-show", help="Show label for a profile")
    p_show.add_argument("profile")
    p_show.set_defaults(func=cmd_label_show)

    p_list = subparsers.add_parser("label-list", help="List all profile labels")
    p_list.set_defaults(func=cmd_label_list)

    p_find = subparsers.add_parser("label-find", help="Find profiles by label/description")
    p_find.add_argument("query")
    p_find.add_argument("--case-sensitive", action="store_true", default=False)
    p_find.set_defaults(func=cmd_label_find)

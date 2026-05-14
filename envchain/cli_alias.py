"""CLI commands for profile alias management."""
from __future__ import annotations

import argparse
import sys

from envchain.alias import (
    AliasError,
    add_alias,
    aliases_for_profile,
    list_aliases,
    remove_alias,
    resolve_alias,
)
from envchain.audit import record_event


def cmd_alias_add(args: argparse.Namespace) -> int:
    """Add or update an alias."""
    try:
        add_alias(args.alias, args.profile)
        record_event("alias_add", args.profile, detail=f"alias={args.alias}")
        print(f"Alias '{args.alias}' -> '{args.profile}' saved.")
        return 0
    except AliasError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_alias_remove(args: argparse.Namespace) -> int:
    """Remove an alias."""
    try:
        remove_alias(args.alias)
        record_event("alias_remove", detail=f"alias={args.alias}")
        print(f"Alias '{args.alias}' removed.")
        return 0
    except AliasError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_alias_resolve(args: argparse.Namespace) -> int:
    """Print the profile name an alias points to."""
    target = resolve_alias(args.alias)
    if target is None:
        print(f"Alias '{args.alias}' not found.", file=sys.stderr)
        return 1
    print(target)
    return 0


def cmd_alias_list(args: argparse.Namespace) -> int:  # noqa: ARG001
    """List all aliases."""
    aliases = list_aliases()
    if not aliases:
        print("No aliases defined.")
        return 0
    for alias, profile in sorted(aliases.items()):
        print(f"{alias:30s}  ->  {profile}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_add = subparsers.add_parser("alias-add", help="Add a profile alias")
    p_add.add_argument("alias")
    p_add.add_argument("profile")
    p_add.set_defaults(func=cmd_alias_add)

    p_rm = subparsers.add_parser("alias-remove", help="Remove a profile alias")
    p_rm.add_argument("alias")
    p_rm.set_defaults(func=cmd_alias_remove)

    p_res = subparsers.add_parser("alias-resolve", help="Resolve an alias to a profile name")
    p_res.add_argument("alias")
    p_res.set_defaults(func=cmd_alias_resolve)

    p_ls = subparsers.add_parser("alias-list", help="List all aliases")
    p_ls.set_defaults(func=cmd_alias_list)

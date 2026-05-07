"""CLI commands for profile tagging."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envchain import tag as tag_mod
from envchain.tag import TagError


def cmd_tag_add(args: argparse.Namespace) -> int:
    try:
        tag_mod.add_tag(args.profile, args.tag)
        print(f"Tag '{args.tag}' added to profile '{args.profile}'.")
        return 0
    except TagError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_tag_remove(args: argparse.Namespace) -> int:
    try:
        tag_mod.remove_tag(args.profile, args.tag)
        print(f"Tag '{args.tag}' removed from profile '{args.profile}'.")
        return 0
    except TagError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_tag_list(args: argparse.Namespace) -> int:
    tags = tag_mod.get_tags(args.profile)
    if not tags:
        print(f"No tags for profile '{args.profile}'.")
    else:
        for t in tags:
            print(t)
    return 0


def cmd_tag_find(args: argparse.Namespace) -> int:
    profiles = tag_mod.profiles_with_tag(args.tag)
    if not profiles:
        print(f"No profiles found with tag '{args.tag}'.")
    else:
        for p in profiles:
            print(p)
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    tag_parser = subparsers.add_parser("tag", help="Manage profile tags")
    tag_sub = tag_parser.add_subparsers(dest="tag_cmd", required=True)

    p_add = tag_sub.add_parser("add", help="Add a tag to a profile")
    p_add.add_argument("profile")
    p_add.add_argument("tag")
    p_add.set_defaults(func=cmd_tag_add)

    p_rm = tag_sub.add_parser("remove", help="Remove a tag from a profile")
    p_rm.add_argument("profile")
    p_rm.add_argument("tag")
    p_rm.set_defaults(func=cmd_tag_remove)

    p_ls = tag_sub.add_parser("list", help="List tags for a profile")
    p_ls.add_argument("profile")
    p_ls.set_defaults(func=cmd_tag_list)

    p_find = tag_sub.add_parser("find", help="Find profiles with a given tag")
    p_find.add_argument("tag")
    p_find.set_defaults(func=cmd_tag_find)

"""CLI commands for profile dependency management."""

from __future__ import annotations

import argparse
import sys

from envchain.dependency import (
    DependencyError,
    add_dependency,
    get_dependencies,
    list_all_dependencies,
    remove_dependency,
    resolve_order,
)


def cmd_dep_add(args: argparse.Namespace) -> int:
    """Add a dependency: envchain dep add <profile> <depends-on>"""
    try:
        add_dependency(args.profile, args.depends_on)
        print(f"Added: {args.profile!r} depends on {args.depends_on!r}")
        return 0
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_dep_remove(args: argparse.Namespace) -> int:
    """Remove a dependency."""
    try:
        remove_dependency(args.profile, args.depends_on)
        print(f"Removed: {args.profile!r} no longer depends on {args.depends_on!r}")
        return 0
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_dep_list(args: argparse.Namespace) -> int:
    """List direct dependencies of a profile."""
    deps = get_dependencies(args.profile)
    if not deps:
        print(f"{args.profile!r} has no declared dependencies.")
    else:
        for d in deps:
            print(d)
    return 0


def cmd_dep_resolve(args: argparse.Namespace) -> int:
    """Print the resolved load order for a profile."""
    try:
        order = resolve_order(args.profile)
        for name in order:
            print(name)
        return 0
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_dep_show_all(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Show the full dependency map."""
    data = list_all_dependencies()
    if not data:
        print("No dependencies defined.")
        return 0
    for profile, deps in sorted(data.items()):
        print(f"{profile}: {', '.join(deps)}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("dep", help="manage profile dependencies")
    sp = p.add_subparsers(dest="dep_cmd", required=True)

    add_p = sp.add_parser("add", help="add a dependency")
    add_p.add_argument("profile")
    add_p.add_argument("depends_on", metavar="depends-on")
    add_p.set_defaults(func=cmd_dep_add)

    rm_p = sp.add_parser("remove", help="remove a dependency")
    rm_p.add_argument("profile")
    rm_p.add_argument("depends_on", metavar="depends-on")
    rm_p.set_defaults(func=cmd_dep_remove)

    ls_p = sp.add_parser("list", help="list dependencies of a profile")
    ls_p.add_argument("profile")
    ls_p.set_defaults(func=cmd_dep_list)

    res_p = sp.add_parser("resolve", help="show resolved load order")
    res_p.add_argument("profile")
    res_p.set_defaults(func=cmd_dep_resolve)

    all_p = sp.add_parser("all", help="show all declared dependencies")
    all_p.set_defaults(func=cmd_dep_show_all)

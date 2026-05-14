"""CLI commands for managing per-profile variable quotas."""

from __future__ import annotations

import argparse
import sys

from envchain.quota import (
    QuotaError,
    QuotaPolicy,
    clear_quota,
    get_quota,
    set_quota,
    _load_quotas,
)


def cmd_quota_set(args: argparse.Namespace) -> int:
    """Set quota limits for a profile."""
    policy = QuotaPolicy(
        max_vars=args.max_vars,
        max_value_bytes=args.max_value_bytes,
        max_total_bytes=args.max_total_bytes,
    )
    try:
        set_quota(args.profile, policy)
    except QuotaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        f"Quota set for '{args.profile}': "
        f"max_vars={policy.max_vars}, "
        f"max_value_bytes={policy.max_value_bytes}, "
        f"max_total_bytes={policy.max_total_bytes}"
    )
    return 0


def cmd_quota_clear(args: argparse.Namespace) -> int:
    """Remove quota limits for a profile."""
    clear_quota(args.profile)
    print(f"Quota cleared for '{args.profile}'.")
    return 0


def cmd_quota_show(args: argparse.Namespace) -> int:
    """Display the quota policy for a profile."""
    policy = get_quota(args.profile)
    if policy is None:
        print(f"No quota set for '{args.profile}'.")
        return 0
    print(f"Profile : {args.profile}")
    print(f"  max_vars        : {policy.max_vars}")
    print(f"  max_value_bytes : {policy.max_value_bytes}")
    print(f"  max_total_bytes : {policy.max_total_bytes}")
    return 0


def cmd_quota_list(args: argparse.Namespace) -> int:  # noqa: ARG001
    """List all profiles that have a quota policy."""
    data = _load_quotas()
    if not data:
        print("No quota policies configured.")
        return 0
    for profile, entry in sorted(data.items()):
        print(
            f"{profile}: max_vars={entry['max_vars']}, "
            f"max_value_bytes={entry['max_value_bytes']}, "
            f"max_total_bytes={entry['max_total_bytes']}"
        )
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p_set = subparsers.add_parser("quota-set", help="Set quota for a profile")
    p_set.add_argument("profile")
    p_set.add_argument("--max-vars", type=int, default=100)
    p_set.add_argument("--max-value-bytes", type=int, default=4096)
    p_set.add_argument("--max-total-bytes", type=int, default=65536)
    p_set.set_defaults(func=cmd_quota_set)

    p_clear = subparsers.add_parser("quota-clear", help="Clear quota for a profile")
    p_clear.add_argument("profile")
    p_clear.set_defaults(func=cmd_quota_clear)

    p_show = subparsers.add_parser("quota-show", help="Show quota for a profile")
    p_show.add_argument("profile")
    p_show.set_defaults(func=cmd_quota_show)

    p_list = subparsers.add_parser("quota-list", help="List all quota policies")
    p_list.set_defaults(func=cmd_quota_list)

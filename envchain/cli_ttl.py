"""CLI commands for managing profile TTLs."""

from __future__ import annotations

import argparse
import sys
from datetime import timezone

from envchain.ttl import TTLError, set_ttl, get_ttl, clear_ttl, is_expired, list_ttls
from envchain.audit import record_event


def cmd_ttl_set(args: argparse.Namespace) -> int:
    """Set a TTL (in seconds) on a profile."""
    try:
        expires_at = set_ttl(args.profile, args.seconds)
    except TTLError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    record_event("ttl_set", args.profile, detail=f"expires={expires_at.isoformat()}")
    print(f"Profile '{args.profile}' will expire at {expires_at.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    return 0


def cmd_ttl_clear(args: argparse.Namespace) -> int:
    """Remove the TTL from a profile."""
    removed = clear_ttl(args.profile)
    if not removed:
        print(f"No TTL set for profile '{args.profile}'.")
        return 0
    record_event("ttl_clear", args.profile)
    print(f"TTL cleared for profile '{args.profile}'.")
    return 0


def cmd_ttl_status(args: argparse.Namespace) -> int:
    """Show TTL status for a profile."""
    expiry = get_ttl(args.profile)
    if expiry is None:
        print(f"No TTL set for profile '{args.profile}'.")
        return 0
    local_exp = expiry.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    expired = is_expired(args.profile)
    status = "EXPIRED" if expired else "active"
    print(f"Profile '{args.profile}': expires {local_exp} [{status}]")
    return 0


def cmd_ttl_list(args: argparse.Namespace) -> int:
    """List all profiles with a TTL."""
    entries = list_ttls()
    if not entries:
        print("No TTL entries found.")
        return 0
    for profile, expiry in sorted(entries.items()):
        local_exp = expiry.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        expired = is_expired(profile)
        flag = " [EXPIRED]" if expired else ""
        print(f"{profile}: {local_exp}{flag}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    ttl_parser = subparsers.add_parser("ttl", help="Manage profile TTLs")
    ttl_sub = ttl_parser.add_subparsers(dest="ttl_cmd", required=True)

    p_set = ttl_sub.add_parser("set", help="Set a TTL on a profile")
    p_set.add_argument("profile")
    p_set.add_argument("seconds", type=int, help="Seconds until expiry")
    p_set.set_defaults(func=cmd_ttl_set)

    p_clear = ttl_sub.add_parser("clear", help="Remove TTL from a profile")
    p_clear.add_argument("profile")
    p_clear.set_defaults(func=cmd_ttl_clear)

    p_status = ttl_sub.add_parser("status", help="Show TTL status for a profile")
    p_status.add_argument("profile")
    p_status.set_defaults(func=cmd_ttl_status)

    p_list = ttl_sub.add_parser("list", help="List all TTL entries")
    p_list.set_defaults(func=cmd_ttl_list)

"""CLI commands for profile locking."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envchain.lock import LockError, get_lock_info, is_locked, lock_profile, unlock_profile
from envchain.audit import record_event


def cmd_lock(args: argparse.Namespace) -> int:
    """Lock a profile, preventing reads and writes."""
    try:
        lock_profile(args.profile, reason=args.reason or "", ttl_seconds=args.ttl)
    except LockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    record_event("lock", args.profile, detail=f"reason={args.reason or 'none'}")
    print(f"Profile '{args.profile}' locked (TTL {args.ttl}s).")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    """Unlock a previously locked profile."""
    try:
        unlock_profile(args.profile)
    except LockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    record_event("unlock", args.profile)
    print(f"Profile '{args.profile}' unlocked.")
    return 0


def cmd_lock_status(args: argparse.Namespace) -> int:
    """Show lock status for a profile."""
    info = get_lock_info(args.profile)
    if info is None:
        print(f"Profile '{args.profile}' is not locked.")
        return 0
    import datetime
    locked_at = datetime.datetime.fromtimestamp(info["locked_at"]).isoformat()
    print(f"Profile '{args.profile}' is LOCKED")
    print(f"  Reason   : {info.get('reason') or '(none)'}")
    print(f"  Locked at: {locked_at}")
    print(f"  TTL      : {info.get('ttl_seconds')}s")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_lock = subparsers.add_parser("lock", help="Lock a profile")
    p_lock.add_argument("profile")
    p_lock.add_argument("--reason", default="", help="Human-readable lock reason")
    p_lock.add_argument("--ttl", type=int, default=3600, help="Lock TTL in seconds (default 3600)")
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = subparsers.add_parser("unlock", help="Unlock a profile")
    p_unlock.add_argument("profile")
    p_unlock.set_defaults(func=cmd_unlock)

    p_status = subparsers.add_parser("lock-status", help="Show lock status for a profile")
    p_status.add_argument("profile")
    p_status.set_defaults(func=cmd_lock_status)

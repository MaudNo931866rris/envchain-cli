"""CLI commands for envchain watch."""

from __future__ import annotations

import argparse
import getpass
import sys

from envchain.watch import WatchError, WatchEvent, watch_profile
from envchain.audit import record_event


def _prompt_passphrase(profile: str) -> str:
    return getpass.getpass(f"Passphrase for profile '{profile}': ")


def cmd_watch(args: argparse.Namespace) -> int:
    """Watch a profile and re-run a command when it changes.

    Usage: envchain watch <profile> -- <command> [args...]
    """
    passphrase = _prompt_passphrase(args.profile)

    interval = getattr(args, "interval", 1.0)

    def _on_change(event: WatchEvent) -> None:
        ts = event.changed_at
        print(
            f"[envchain-watch] Profile '{event.profile}' changed "
            f"(mtime {event.previous_mtime:.0f} -> {event.current_mtime:.0f}). "
            "Re-running command...",
            file=sys.stderr,
        )
        record_event(
            action="watch_trigger",
            profile=event.profile,
            detail=f"mtime_changed:{event.current_mtime:.0f}",
        )

    try:
        print(
            f"[envchain-watch] Watching '{args.profile}' every {interval}s. "
            "Press Ctrl-C to stop.",
            file=sys.stderr,
        )
        watch_profile(
            profile=args.profile,
            passphrase=passphrase,
            command=args.command,
            interval=interval,
            on_change=_on_change,
        )
    except WatchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[envchain-watch] Stopped.", file=sys.stderr)

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watch",
        help="Re-run a command whenever a profile changes.",
    )
    p.add_argument("profile", help="Profile to watch.")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run on change (prefix with -- if needed).",
    )
    p.set_defaults(func=cmd_watch)

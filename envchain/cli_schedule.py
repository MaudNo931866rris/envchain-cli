"""CLI commands for managing profile schedules."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from envchain.schedule import (
    ScheduleError,
    set_schedule,
    get_schedule,
    clear_schedule,
    list_schedules,
    due_schedules,
)


def cmd_schedule_set(args: argparse.Namespace) -> int:
    """Set a recurring schedule for a profile action."""
    try:
        next_run = set_schedule(args.profile, args.interval_days, args.action)
        print(f"Scheduled '{args.action}' for '{args.profile}' every {args.interval_days} day(s).")
        print(f"Next run: {next_run.isoformat()}")
        return 0
    except ScheduleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_schedule_clear(args: argparse.Namespace) -> int:
    """Remove a schedule for a profile."""
    removed = clear_schedule(args.profile)
    if removed:
        print(f"Schedule cleared for '{args.profile}'.")
        return 0
    print(f"No schedule found for '{args.profile}'.", file=sys.stderr)
    return 1


def cmd_schedule_show(args: argparse.Namespace) -> int:
    """Show the schedule for a specific profile."""
    entry = get_schedule(args.profile)
    if entry is None:
        print(f"No schedule set for '{args.profile}'.")
        return 0
    print(f"Profile:      {args.profile}")
    print(f"Action:       {entry['action']}")
    print(f"Interval:     {entry['interval_days']} day(s)")
    print(f"Next run:     {entry['next_run']}")
    print(f"Created at:   {entry['created_at']}")
    return 0


def cmd_schedule_list(args: argparse.Namespace) -> int:
    """List all scheduled profiles."""
    entries = list_schedules()
    if not entries:
        print("No schedules configured.")
        return 0
    for e in entries:
        print(f"{e['profile']:30s}  {e['action']:8s}  every {e['interval_days']}d  next: {e['next_run']}")
    return 0


def cmd_schedule_due(args: argparse.Namespace) -> int:
    """List schedules that are currently due."""
    entries = due_schedules()
    if not entries:
        print("No schedules are currently due.")
        return 0
    for e in entries:
        print(f"{e['profile']:30s}  {e['action']:8s}  due since {e['next_run']}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_set = subparsers.add_parser("schedule-set", help="Schedule a recurring action for a profile")
    p_set.add_argument("profile")
    p_set.add_argument("interval_days", type=int)
    p_set.add_argument("--action", default="rotate", choices=["rotate", "expire", "remind"])
    p_set.set_defaults(func=cmd_schedule_set)

    p_clear = subparsers.add_parser("schedule-clear", help="Remove a profile schedule")
    p_clear.add_argument("profile")
    p_clear.set_defaults(func=cmd_schedule_clear)

    p_show = subparsers.add_parser("schedule-show", help="Show schedule for a profile")
    p_show.add_argument("profile")
    p_show.set_defaults(func=cmd_schedule_show)

    p_list = subparsers.add_parser("schedule-list", help="List all schedules")
    p_list.set_defaults(func=cmd_schedule_list)

    p_due = subparsers.add_parser("schedule-due", help="List due schedules")
    p_due.set_defaults(func=cmd_schedule_due)

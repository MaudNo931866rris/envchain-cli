"""CLI commands for the audit-log feature."""

from __future__ import annotations

import json
from typing import List

from envchain import audit


def cmd_audit_log(profile: str | None, output_format: str = "text") -> int:
    """
    Print audit events to stdout.

    Args:
        profile: If given, filter events to this profile name.
        output_format: 'text' (default) or 'json'.

    Returns:
        0 on success, 1 if no events found.
    """
    events = audit.read_events(profile=profile)

    if not events:
        label = f"profile '{profile}'" if profile else "any profile"
        print(f"No audit events found for {label}.")
        return 1

    if output_format == "json":
        print(json.dumps(events, indent=2))
    else:
        for ev in events:
            detail = f"  [{ev['detail']}]" if ev.get("detail") else ""
            print(f"{ev['ts']}  {ev['action']:12s}  {ev['profile']}{detail}")

    return 0


def cmd_audit_clear(confirm: bool = False) -> int:
    """
    Clear the entire audit log.

    Args:
        confirm: Must be True to proceed (safety guard).

    Returns:
        0 on success, 1 if not confirmed.
    """
    if not confirm:
        print("Pass --confirm to erase the audit log.")
        return 1

    audit.clear_log()
    print("Audit log cleared.")
    return 0


def cmd_audit_stats(profile: str | None = None) -> int:
    """
    Print a summary of audit event counts grouped by action.

    Args:
        profile: If given, restrict stats to this profile name.

    Returns:
        0 on success, 1 if no events found.
    """
    events = audit.read_events(profile=profile)

    if not events:
        label = f"profile '{profile}'" if profile else "any profile"
        print(f"No audit events found for {label}.")
        return 1

    counts: dict[str, int] = {}
    for ev in events:
        counts[ev["action"]] = counts.get(ev["action"], 0) + 1

    label = f" (profile: {profile})" if profile else ""
    print(f"Audit log summary{label}:")
    for action, count in sorted(counts.items()):
        print(f"  {action:12s}  {count}")
    print(f"  {'TOTAL':12s}  {len(events)}")

    return 0

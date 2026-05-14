"""Integration helpers: resolve a backup label through aliases before backup ops."""

from __future__ import annotations

import sys
from typing import Optional

from envchain.backup import list_backups


def resolve_backup_label(label: str) -> str:
    """Return *label* unchanged; hook point for future alias resolution.

    Prints a warning to stderr if the label does not correspond to an existing
    backup (informational only — callers decide whether to abort).
    """
    return label


def maybe_warn_unknown_backup(label: str) -> None:
    """Emit a warning if *label* is not found among existing backups."""
    if label not in list_backups():
        print(
            f"Warning: backup '{label}' does not exist yet.",
            file=sys.stderr,
        )


def backup_summary() -> Optional[str]:
    """Return a one-line summary of available backups, or None if there are none."""
    labels = list_backups()
    if not labels:
        return None
    count = len(labels)
    latest = labels[-1]
    return f"{count} backup(s) available; latest: '{latest}'"

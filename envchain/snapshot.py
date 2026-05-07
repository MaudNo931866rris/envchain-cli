"""Snapshot: capture and restore point-in-time copies of a profile's variables."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from envchain.store import _store_dir


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(profile_name: str) -> str:
    d = os.path.join(_store_dir(), ".snapshots", profile_name)
    os.makedirs(d, exist_ok=True)
    return d


def _snapshot_path(profile_name: str, label: str) -> str:
    return os.path.join(_snapshot_dir(profile_name), f"{label}.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Snapshot:
    profile: str
    label: str
    created_at: str
    variables: Dict[str, str] = field(default_factory=dict)


def save_snapshot(profile_name: str, variables: Dict[str, str], label: str) -> Snapshot:
    """Persist a snapshot of *variables* for *profile_name* under *label*."""
    path = _snapshot_path(profile_name, label)
    if os.path.exists(path):
        raise SnapshotError(f"Snapshot '{label}' already exists for profile '{profile_name}'")
    snap = Snapshot(profile=profile_name, label=label, created_at=_now_iso(), variables=dict(variables))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"profile": snap.profile, "label": snap.label,
                   "created_at": snap.created_at, "variables": snap.variables}, fh, indent=2)
    return snap


def load_snapshot(profile_name: str, label: str) -> Snapshot:
    """Load a previously saved snapshot."""
    path = _snapshot_path(profile_name, label)
    if not os.path.exists(path):
        raise SnapshotError(f"Snapshot '{label}' not found for profile '{profile_name}'")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot(**data)


def list_snapshots(profile_name: str) -> List[str]:
    """Return labels of all snapshots for *profile_name*, sorted by name."""
    d = _snapshot_dir(profile_name)
    return sorted(
        f[:-5] for f in os.listdir(d) if f.endswith(".json")
    )


def delete_snapshot(profile_name: str, label: str) -> None:
    """Remove a snapshot file."""
    path = _snapshot_path(profile_name, label)
    if not os.path.exists(path):
        raise SnapshotError(f"Snapshot '{label}' not found for profile '{profile_name}'")
    os.remove(path)

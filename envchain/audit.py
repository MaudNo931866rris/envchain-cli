"""Audit log for envchain profile access and modifications."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

_LOG_FILENAME = "audit.log"


def _log_path() -> Path:
    base = Path(os.environ.get("ENVCHAIN_DIR", Path.home() / ".envchain"))
    base.mkdir(parents=True, exist_ok=True)
    return base / _LOG_FILENAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_event(action: str, profile: str, detail: str = "") -> None:
    """Append a single audit event to the log file."""
    entry: Dict[str, Any] = {
        "ts": _now_iso(),
        "action": action,
        "profile": profile,
    }
    if detail:
        entry["detail"] = detail

    with _log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_events(profile: str | None = None) -> List[Dict[str, Any]]:
    """Return all audit events, optionally filtered by profile name."""
    path = _log_path()
    if not path.exists():
        return []

    events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if profile is None or entry.get("profile") == profile:
                events.append(entry)
    return events


def clear_log() -> None:
    """Erase the entire audit log (used in tests / admin reset)."""
    path = _log_path()
    if path.exists():
        path.unlink()

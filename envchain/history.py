"""Track value change history for profile variables."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envchain.store import _store_dir


class HistoryError(Exception):
    pass


def _history_path(profile: str) -> Path:
    return _store_dir() / f"{profile}.history.json"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class HistoryEntry:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    action: str  # 'set' | 'unset'
    timestamp: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "action": self.action,
            "timestamp": self.timestamp,
        }


def _load_history(profile: str) -> List[dict]:
    path = _history_path(profile)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise HistoryError(f"Failed to read history for '{profile}': {exc}") from exc


def _save_history(profile: str, entries: List[dict]) -> None:
    path = _history_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_change(
    profile: str,
    key: str,
    old_value: Optional[str],
    new_value: Optional[str],
    action: str,
) -> HistoryEntry:
    """Append a variable change event to the profile's history log."""
    if action not in ("set", "unset"):
        raise HistoryError(f"Invalid action '{action}'; must be 'set' or 'unset'")
    entry = HistoryEntry(
        key=key, old_value=old_value, new_value=new_value, action=action
    )
    entries = _load_history(profile)
    entries.append(entry.as_dict())
    _save_history(profile, entries)
    return entry


def get_history(
    profile: str, key: Optional[str] = None, limit: Optional[int] = None
) -> List[HistoryEntry]:
    """Return history entries, optionally filtered by key and capped by limit."""
    raw = _load_history(profile)
    if key is not None:
        raw = [r for r in raw if r["key"] == key]
    if limit is not None:
        raw = raw[-limit:]
    return [
        HistoryEntry(
            key=r["key"],
            old_value=r["old_value"],
            new_value=r["new_value"],
            action=r["action"],
            timestamp=r["timestamp"],
        )
        for r in raw
    ]


def clear_history(profile: str) -> None:
    """Delete the history log for a profile."""
    path = _history_path(profile)
    if path.exists():
        path.unlink()

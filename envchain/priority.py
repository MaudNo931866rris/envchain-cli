"""Profile priority management — assign and query numeric priority levels for profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class PriorityError(Exception):
    pass


def _priority_path() -> Path:
    return _store_dir() / "priorities.json"


def _load_priorities() -> dict[str, int]:
    p = _priority_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_priorities(data: dict[str, int]) -> None:
    _priority_path().write_text(json.dumps(data, indent=2))


def set_priority(profile: str, level: int) -> int:
    """Assign a numeric priority level to *profile*. Returns the level set."""
    if not profile:
        raise PriorityError("Profile name must not be empty.")
    if not isinstance(level, int):
        raise PriorityError("Priority level must be an integer.")
    data = _load_priorities()
    data[profile] = level
    _save_priorities(data)
    return level


def get_priority(profile: str) -> Optional[int]:
    """Return the priority level for *profile*, or None if not set."""
    return _load_priorities().get(profile)


def clear_priority(profile: str) -> bool:
    """Remove priority entry for *profile*. Returns True if it existed."""
    data = _load_priorities()
    if profile not in data:
        return False
    del data[profile]
    _save_priorities(data)
    return True


def list_priorities() -> list[tuple[str, int]]:
    """Return all (profile, level) pairs sorted by level descending, then name."""
    data = _load_priorities()
    return sorted(data.items(), key=lambda kv: (-kv[1], kv[0]))

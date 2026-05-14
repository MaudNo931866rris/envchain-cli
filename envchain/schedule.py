"""Schedule automatic profile rotation reminders and expiry checks."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class ScheduleError(Exception):
    pass


def _schedule_path() -> Path:
    p = _store_dir() / "schedules.json"
    return p


def _load_schedules() -> dict:
    p = _schedule_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_schedules(data: dict) -> None:
    _schedule_path().write_text(json.dumps(data, indent=2))


def _now() -> datetime:
    return datetime.utcnow()


def set_schedule(profile: str, interval_days: int, action: str = "rotate") -> datetime:
    """Schedule a recurring action for a profile."""
    if not profile:
        raise ScheduleError("Profile name must not be empty.")
    if interval_days <= 0:
        raise ScheduleError("interval_days must be a positive integer.")
    if action not in ("rotate", "expire", "remind"):
        raise ScheduleError(f"Unknown action '{action}'. Choose rotate, expire, or remind.")
    data = _load_schedules()
    next_run = _now() + timedelta(days=interval_days)
    data[profile] = {
        "action": action,
        "interval_days": interval_days,
        "next_run": next_run.isoformat(),
        "created_at": _now().isoformat(),
    }
    _save_schedules(data)
    return next_run


def get_schedule(profile: str) -> Optional[dict]:
    """Return the schedule entry for a profile, or None."""
    return _load_schedules().get(profile)


def clear_schedule(profile: str) -> bool:
    """Remove a schedule entry. Returns True if removed, False if not found."""
    data = _load_schedules()
    if profile not in data:
        return False
    del data[profile]
    _save_schedules(data)
    return True


def list_schedules() -> list[dict]:
    """Return all scheduled profiles as a list of dicts."""
    data = _load_schedules()
    return [
        {"profile": k, **v}
        for k, v in sorted(data.items())
    ]


def due_schedules() -> list[dict]:
    """Return schedules whose next_run is at or before now."""
    now = _now()
    return [
        entry for entry in list_schedules()
        if datetime.fromisoformat(entry["next_run"]) <= now
    ]

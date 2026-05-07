"""Profile locking: temporarily lock a profile so it cannot be read or modified."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class LockError(Exception):
    """Raised when a lock operation fails."""


def _lock_path(profile: str) -> Path:
    return _store_dir() / f"{profile}.lock"


def _now() -> float:
    return time.time()


def lock_profile(profile: str, reason: str = "", ttl_seconds: int = 3600) -> None:
    """Create a lock file for *profile*.

    Raises LockError if the profile is already locked.
    """
    path = _lock_path(profile)
    if path.exists():
        info = _read_lock(path)
        raise LockError(
            f"Profile '{profile}' is already locked (reason: {info.get('reason', 'none')})"
        )
    payload = {
        "profile": profile,
        "reason": reason,
        "locked_at": _now(),
        "ttl_seconds": ttl_seconds,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def unlock_profile(profile: str) -> None:
    """Remove the lock file for *profile*.

    Raises LockError if the profile is not locked.
    """
    path = _lock_path(profile)
    if not path.exists():
        raise LockError(f"Profile '{profile}' is not locked")
    path.unlink()


def is_locked(profile: str) -> bool:
    """Return True if *profile* currently has an active (non-expired) lock."""
    path = _lock_path(profile)
    if not path.exists():
        return False
    info = _read_lock(path)
    age = _now() - info.get("locked_at", 0)
    if age > info.get("ttl_seconds", 3600):
        path.unlink(missing_ok=True)
        return False
    return True


def get_lock_info(profile: str) -> Optional[dict]:
    """Return lock metadata for *profile*, or None if not locked."""
    path = _lock_path(profile)
    if not path.exists():
        return None
    info = _read_lock(path)
    age = _now() - info.get("locked_at", 0)
    if age > info.get("ttl_seconds", 3600):
        path.unlink(missing_ok=True)
        return None
    return info


def _read_lock(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

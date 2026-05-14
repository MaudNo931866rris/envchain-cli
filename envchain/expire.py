"""Profile expiry: set an expiration date on a profile after which it cannot be loaded."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class ExpireError(Exception):
    pass


def _expire_path() -> Path:
    return _store_dir() / "expiry.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_expiry() -> dict:
    p = _expire_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_expiry(data: dict) -> None:
    _expire_path().write_text(json.dumps(data, indent=2))


def set_expiry(profile: str, expires_at: datetime) -> datetime:
    """Set an expiration datetime (UTC) for *profile*.

    Raises ExpireError if *expires_at* is in the past.
    """
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _now():
        raise ExpireError("Expiration datetime must be in the future.")
    data = _load_expiry()
    data[profile] = expires_at.isoformat()
    _save_expiry(data)
    return expires_at


def get_expiry(profile: str) -> Optional[datetime]:
    """Return the expiration datetime for *profile*, or None if not set."""
    data = _load_expiry()
    raw = data.get(profile)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def clear_expiry(profile: str) -> bool:
    """Remove expiry for *profile*. Returns True if an entry was removed."""
    data = _load_expiry()
    if profile not in data:
        return False
    del data[profile]
    _save_expiry(data)
    return True


def is_expired(profile: str) -> bool:
    """Return True if *profile* has an expiry set and that time has passed."""
    expiry = get_expiry(profile)
    if expiry is None:
        return False
    return _now() >= expiry


def list_expiry() -> dict[str, datetime]:
    """Return a mapping of profile name -> expiration datetime for all entries."""
    data = _load_expiry()
    return {name: datetime.fromisoformat(ts) for name, ts in data.items()}

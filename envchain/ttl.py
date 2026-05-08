"""TTL (time-to-live) expiry support for profiles."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class TTLError(Exception):
    pass


def _ttl_path() -> Path:
    return _store_dir() / "ttl.json"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _load_ttl() -> dict:
    p = _ttl_path()
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_ttl(data: dict) -> None:
    p = _ttl_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_ttl(profile: str, seconds: int) -> datetime:
    """Set an expiry for *profile* that fires *seconds* from now."""
    if seconds <= 0:
        raise TTLError("seconds must be a positive integer")
    expires_at = _now() + timedelta(seconds=seconds)
    data = _load_ttl()
    data[profile] = expires_at.isoformat()
    _save_ttl(data)
    return expires_at


def get_ttl(profile: str) -> Optional[datetime]:
    """Return the expiry datetime for *profile*, or None if not set."""
    data = _load_ttl()
    raw = data.get(profile)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def clear_ttl(profile: str) -> bool:
    """Remove any TTL for *profile*. Returns True if an entry existed."""
    data = _load_ttl()
    if profile not in data:
        return False
    del data[profile]
    _save_ttl(data)
    return True


def is_expired(profile: str) -> bool:
    """Return True if the profile has a TTL that has already passed."""
    expiry = get_ttl(profile)
    if expiry is None:
        return False
    return _now() >= expiry


def list_ttls() -> dict[str, datetime]:
    """Return a mapping of profile -> expiry datetime for all TTL entries."""
    data = _load_ttl()
    return {k: datetime.fromisoformat(v) for k, v in data.items()}

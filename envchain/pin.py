"""Profile PIN protection: require a short numeric PIN before decrypting a profile."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from envchain.store import _store_dir


class PinError(Exception):
    """Raised when a PIN operation fails."""


def _pins_path() -> Path:
    return _store_dir() / "pins.json"


def _load_pins() -> dict[str, str]:
    p = _pins_path()
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_pins(pins: dict[str, str]) -> None:
    p = _pins_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(pins, fh, indent=2)
    os.chmod(p, 0o600)


def _hash_pin(pin: str) -> str:
    """Return a SHA-256 hex digest of the PIN (no salt needed for short-circuit protection)."""
    return hashlib.sha256(pin.encode()).hexdigest()


def set_pin(profile: str, pin: str) -> None:
    """Attach a PIN to *profile*. Raises PinError if PIN is not 4-8 digits."""
    if not pin.isdigit() or not (4 <= len(pin) <= 8):
        raise PinError("PIN must be 4-8 numeric digits.")
    pins = _load_pins()
    pins[profile] = _hash_pin(pin)
    _save_pins(pins)


def clear_pin(profile: str) -> None:
    """Remove the PIN for *profile*. No-op if no PIN is set."""
    pins = _load_pins()
    pins.pop(profile, None)
    _save_pins(pins)


def has_pin(profile: str) -> bool:
    """Return True if *profile* has a PIN configured."""
    return profile in _load_pins()


def verify_pin(profile: str, pin: str) -> bool:
    """Return True if *pin* matches the stored PIN for *profile*."""
    pins = _load_pins()
    if profile not in pins:
        return True  # no PIN set — always passes
    return pins[profile] == _hash_pin(pin)


def require_pin(profile: str, pin: str) -> None:
    """Raise PinError if *pin* does not match the stored PIN for *profile*."""
    if not verify_pin(profile, pin):
        raise PinError(f"Incorrect PIN for profile '{profile}'.")

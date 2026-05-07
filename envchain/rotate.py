"""Passphrase rotation for encrypted profiles."""

from __future__ import annotations

from typing import Optional

from envchain.store import load_profile, save_profile
from envchain.audit import record_event
from envchain.lock import is_locked


class RotateError(Exception):
    """Raised when passphrase rotation fails."""


def rotate_passphrase(
    profile_name: str,
    old_passphrase: str,
    new_passphrase: str,
    *,
    audit: bool = True,
) -> None:
    """Re-encrypt *profile_name* under *new_passphrase*.

    Loads the profile with *old_passphrase*, verifies decryption succeeds,
    then immediately re-saves with *new_passphrase*.

    Raises
    ------
    RotateError
        If the profile is locked, the old passphrase is wrong, or the new
        passphrase is identical to the old one.
    """
    if old_passphrase == new_passphrase:
        raise RotateError("New passphrase must differ from the current passphrase.")

    if is_locked(profile_name):
        raise RotateError(
            f"Profile '{profile_name}' is locked. Unlock it before rotating."
        )

    try:
        data = load_profile(profile_name, old_passphrase)
    except Exception as exc:  # noqa: BLE001
        raise RotateError(
            f"Could not decrypt profile '{profile_name}': {exc}"
        ) from exc

    try:
        save_profile(profile_name, data, new_passphrase)
    except Exception as exc:  # noqa: BLE001
        raise RotateError(
            f"Failed to re-encrypt profile '{profile_name}': {exc}"
        ) from exc

    if audit:
        record_event(
            "rotate",
            profile_name,
            detail="passphrase rotated",
        )

"""Rename a profile (change its name/key in the store)."""

from __future__ import annotations

from envchain import store
from envchain.profile import Profile


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_profile(old_name: str, new_name: str, passphrase: str) -> None:
    """Rename *old_name* to *new_name*, re-encrypting under the same passphrase.

    Raises
    ------
    RenameError
        If *old_name* does not exist or *new_name* already exists.
    ValueError
        If the passphrase is wrong (propagated from :mod:`envchain.store`).
    """
    if old_name == new_name:
        raise RenameError("Source and destination names are identical.")

    existing = store.list_profiles()

    if old_name not in existing:
        raise RenameError(f"Profile '{old_name}' does not exist.")

    if new_name in existing:
        raise RenameError(
            f"Profile '{new_name}' already exists. "
            "Delete it first or choose a different name."
        )

    # Load the source profile (validates passphrase)
    raw: dict[str, str] = store.load_profile(old_name, passphrase)

    # Build a new Profile object with the new name and save it
    profile = Profile(name=new_name, vars=raw)
    profile.save(passphrase)

    # Remove the old profile file
    store.delete_profile(old_name)

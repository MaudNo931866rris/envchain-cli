"""Copy or rename variables between profiles."""

from __future__ import annotations

from typing import Optional

from envchain.profile import Profile, load, save, set_var, unset_var


class CopyError(Exception):
    """Raised when a copy or rename operation fails."""


def copy_var(
    src_profile: str,
    src_key: str,
    dst_profile: str,
    dst_key: str,
    passphrase: str,
    *,
    overwrite: bool = False,
) -> None:
    """Copy *src_key* from *src_profile* into *dst_profile* as *dst_key*.

    Both profiles are unlocked with the same *passphrase*.
    Raises ``CopyError`` if the source key does not exist, or if the
    destination key already exists and *overwrite* is False.
    """
    src = load(src_profile, passphrase)
    env = src.as_env_dict()

    if src_key not in env:
        raise CopyError(
            f"Key '{src_key}' not found in profile '{src_profile}'."
        )

    value = env[src_key]

    # Load or create the destination profile.
    try:
        dst = load(dst_profile, passphrase)
    except FileNotFoundError:
        dst = Profile(name=dst_profile)

    if dst_key in dst.as_env_dict() and not overwrite:
        raise CopyError(
            f"Key '{dst_key}' already exists in profile '{dst_profile}'. "
            "Pass overwrite=True to replace it."
        )

    set_var(dst, dst_key, value)
    save(dst, passphrase)


def move_var(
    src_profile: str,
    src_key: str,
    dst_profile: str,
    dst_key: str,
    passphrase: str,
    *,
    overwrite: bool = False,
) -> None:
    """Move *src_key* from *src_profile* to *dst_profile* as *dst_key*.

    Equivalent to ``copy_var`` followed by removing the source key.
    """
    copy_var(
        src_profile,
        src_key,
        dst_profile,
        dst_key,
        passphrase,
        overwrite=overwrite,
    )

    src = load(src_profile, passphrase)
    unset_var(src, src_key)
    save(src, passphrase)

"""Clone (deep-copy) an existing profile under a new name."""

from __future__ import annotations

from typing import Optional

from envchain.profile import Profile, load, save


class CloneError(Exception):
    """Raised when a clone operation cannot be completed."""


def clone_profile(
    src_name: str,
    dst_name: str,
    passphrase: str,
    *,
    dst_passphrase: Optional[str] = None,
    overwrite: bool = False,
) -> Profile:
    """Clone *src_name* into a new profile called *dst_name*.

    Parameters
    ----------
    src_name:       Name of the source profile.
    dst_name:       Name of the destination profile.
    passphrase:     Passphrase used to decrypt the source profile.
    dst_passphrase: Passphrase for the new profile.  Defaults to *passphrase*.
    overwrite:      When *True* an existing destination profile is silently
                    replaced; when *False* (default) a :class:`CloneError` is
                    raised instead.

    Returns
    -------
    Profile
        The newly created destination profile (already persisted to disk).
    """
    if src_name == dst_name:
        raise CloneError("Source and destination profile names must differ.")

    # Load source – propagates InvalidToken / FileNotFoundError on bad input.
    src_profile: Profile = load(src_name, passphrase)

    # Guard against accidental overwrites.
    if not overwrite:
        try:
            load(dst_name, passphrase if dst_passphrase is None else dst_passphrase)
            raise CloneError(
                f"Profile '{dst_name}' already exists. "
                "Use overwrite=True to replace it."
            )
        except (FileNotFoundError, Exception) as exc:
            # Re-raise only our own CloneError; anything else means the
            # destination does not exist or could not be decrypted — fine.
            if isinstance(exc, CloneError):
                raise

    target_pass = dst_passphrase if dst_passphrase is not None else passphrase

    dst_profile = Profile(name=dst_name)
    for key, value in src_profile.as_env_dict().items():
        dst_profile.set_var(key, value)

    save(dst_profile, target_pass)
    return dst_profile

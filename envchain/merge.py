"""Merge variables from one or more source profiles into a destination profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envchain.profile import load, save, Profile


class MergeError(Exception):
    """Raised when a merge operation cannot be completed."""


@dataclass
class MergeResult:
    destination: str
    merged_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)
    overwritten_keys: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return {
            "destination": self.destination,
            "merged_keys": self.merged_keys,
            "skipped_keys": self.skipped_keys,
            "overwritten_keys": self.overwritten_keys,
        }


def merge_profiles(
    source_names: List[str],
    destination_name: str,
    src_passphrase: str,
    dst_passphrase: str,
    overwrite: bool = False,
) -> MergeResult:
    """Merge variables from *source_names* into *destination_name*.

    Args:
        source_names: Ordered list of profile names to read from.
        destination_name: Profile that receives the merged variables.
        src_passphrase: Passphrase used to decrypt every source profile.
        dst_passphrase: Passphrase used to decrypt/encrypt the destination.
        overwrite: When *True*, source values overwrite existing destination keys.

    Returns:
        A :class:`MergeResult` describing what happened.

    Raises:
        MergeError: If a source profile does not exist or decryption fails.
    """
    if not source_names:
        raise MergeError("At least one source profile must be specified.")

    if destination_name in source_names:
        raise MergeError(
            f"Destination profile '{destination_name}' must not appear in sources."
        )

    # Load or create destination
    try:
        dst_profile = load(destination_name, dst_passphrase)
    except FileNotFoundError:
        dst_profile = Profile(name=destination_name, passphrase=dst_passphrase)

    result = MergeResult(destination=destination_name)

    for src_name in source_names:
        try:
            src_profile = load(src_name, src_passphrase)
        except FileNotFoundError:
            raise MergeError(f"Source profile '{src_name}' does not exist.")
        except Exception as exc:  # pragma: no cover
            raise MergeError(f"Failed to load source profile '{src_name}': {exc}") from exc

        for key, value in src_profile.as_env_dict().items():
            if key in dst_profile.as_env_dict():
                if overwrite:
                    dst_profile.set_var(key, value)
                    result.overwritten_keys.append(key)
                else:
                    result.skipped_keys.append(key)
            else:
                dst_profile.set_var(key, value)
                result.merged_keys.append(key)

    save(dst_profile)
    return result

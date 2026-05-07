"""Compare two profiles and report differences in their variable sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.profile import load


class DiffError(Exception):
    """Raised when a diff operation cannot be completed."""


@dataclass
class VarDiff:
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "status": self.status,
            "left_value": self.left_value,
            "right_value": self.right_value,
        }


@dataclass
class ProfileDiff:
    left_profile: str
    right_profile: str
    entries: List[VarDiff] = field(default_factory=list)

    # Convenience views
    @property
    def added(self) -> List[VarDiff]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[VarDiff]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[VarDiff]:
        return [e for e in self.entries if e.status == "changed"]

    @property
    def unchanged(self) -> List[VarDiff]:
        return [e for e in self.entries if e.status == "unchanged"]

    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_profiles(
    left_name: str,
    right_name: str,
    passphrase: str,
    *,
    include_unchanged: bool = False,
) -> ProfileDiff:
    """Load two profiles and return a :class:`ProfileDiff` describing their differences."""
    try:
        left_profile = load(left_name, passphrase)
    except Exception as exc:
        raise DiffError(f"Cannot load profile '{left_name}': {exc}") from exc

    try:
        right_profile = load(right_name, passphrase)
    except Exception as exc:
        raise DiffError(f"Cannot load profile '{right_name}': {exc}") from exc

    left_vars: Dict[str, str] = left_profile.as_env_dict()
    right_vars: Dict[str, str] = right_profile.as_env_dict()

    all_keys = sorted(set(left_vars) | set(right_vars))
    entries: List[VarDiff] = []

    for key in all_keys:
        in_left = key in left_vars
        in_right = key in right_vars

        if in_left and not in_right:
            entries.append(VarDiff(key, "removed", left_value=left_vars[key]))
        elif in_right and not in_left:
            entries.append(VarDiff(key, "added", right_value=right_vars[key]))
        elif left_vars[key] != right_vars[key]:
            entries.append(
                VarDiff(key, "changed", left_value=left_vars[key], right_value=right_vars[key])
            )
        elif include_unchanged:
            entries.append(
                VarDiff(key, "unchanged", left_value=left_vars[key], right_value=right_vars[key])
            )

    return ProfileDiff(left_name, right_name, entries)

"""Per-profile variable count and value size quota enforcement."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class QuotaError(Exception):
    """Raised when a quota limit is exceeded or an operation fails."""


_DEFAULT_MAX_VARS = 100
_DEFAULT_MAX_VALUE_BYTES = 4096
_DEFAULT_MAX_TOTAL_BYTES = 65536


def _quota_path() -> Path:
    return _store_dir() / "quotas.json"


def _load_quotas() -> dict:
    p = _quota_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_quotas(data: dict) -> None:
    _quota_path().write_text(json.dumps(data, indent=2))


@dataclass
class QuotaPolicy:
    max_vars: int = _DEFAULT_MAX_VARS
    max_value_bytes: int = _DEFAULT_MAX_VALUE_BYTES
    max_total_bytes: int = _DEFAULT_MAX_TOTAL_BYTES


def set_quota(profile: str, policy: QuotaPolicy) -> None:
    """Persist a quota policy for *profile*."""
    if not profile:
        raise QuotaError("Profile name must not be empty.")
    data = _load_quotas()
    data[profile] = {
        "max_vars": policy.max_vars,
        "max_value_bytes": policy.max_value_bytes,
        "max_total_bytes": policy.max_total_bytes,
    }
    _save_quotas(data)


def get_quota(profile: str) -> Optional[QuotaPolicy]:
    """Return the quota policy for *profile*, or *None* if not set."""
    data = _load_quotas()
    entry = data.get(profile)
    if entry is None:
        return None
    return QuotaPolicy(**entry)


def clear_quota(profile: str) -> None:
    """Remove the quota policy for *profile*."""
    data = _load_quotas()
    data.pop(profile, None)
    _save_quotas(data)


def check_quota(profile: str, vars_: dict[str, str]) -> None:
    """Raise *QuotaError* if *vars_* would violate the policy for *profile*."""
    policy = get_quota(profile)
    if policy is None:
        return
    if len(vars_) > policy.max_vars:
        raise QuotaError(
            f"Profile '{profile}' exceeds max variable count "
            f"({len(vars_)} > {policy.max_vars})."
        )
    for key, value in vars_.items():
        size = len(value.encode())
        if size > policy.max_value_bytes:
            raise QuotaError(
                f"Variable '{key}' in profile '{profile}' exceeds max value size "
                f"({size} > {policy.max_value_bytes} bytes)."
            )
    total = sum(len(v.encode()) for v in vars_.values())
    if total > policy.max_total_bytes:
        raise QuotaError(
            f"Profile '{profile}' exceeds max total size "
            f"({total} > {policy.max_total_bytes} bytes)."
        )

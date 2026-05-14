"""Integration helpers: resolve an alias before running a profile command.

This module is intentionally small — it provides a single utility used by
other CLI entry-points to transparently substitute an alias for a real
profile name before any store operation occurs.
"""
from __future__ import annotations

from typing import Optional

from envchain.alias import resolve_alias


def resolve_profile_name(name: str) -> str:
    """Return the canonical profile name for *name*.

    If *name* is a registered alias the mapped profile name is returned;
    otherwise *name* itself is returned unchanged.  This makes alias
    resolution completely transparent to callers.

    >>> resolve_profile_name("prod")  # 'prod' not an alias → returned as-is
    'prod'
    """
    resolved: Optional[str] = resolve_alias(name)
    return resolved if resolved is not None else name


def maybe_warn_alias(name: str, original: str) -> None:  # pragma: no cover
    """Print a hint when *name* was resolved from alias *original*.

    Callers may choose to skip this in non-interactive contexts.
    """
    if name != original:
        print(f"[envchain] Note: '{original}' is an alias for '{name}'.")

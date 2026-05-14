"""Profile alias management — assign short names to profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envchain.store import _store_dir


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _aliases_path() -> Path:
    return _store_dir() / "aliases.json"


def _load_aliases() -> Dict[str, str]:
    path = _aliases_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_aliases(aliases: Dict[str, str]) -> None:
    _aliases_path().write_text(json.dumps(aliases, indent=2))


def add_alias(alias: str, profile_name: str) -> None:
    """Map *alias* to *profile_name*, overwriting any previous mapping."""
    if not alias.strip():
        raise AliasError("Alias must not be empty.")
    if not profile_name.strip():
        raise AliasError("Profile name must not be empty.")
    aliases = _load_aliases()
    aliases[alias] = profile_name
    _save_aliases(aliases)


def remove_alias(alias: str) -> None:
    """Remove *alias*; raises AliasError if it does not exist."""
    aliases = _load_aliases()
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    del aliases[alias]
    _save_aliases(aliases)


def resolve_alias(alias: str) -> Optional[str]:
    """Return the profile name for *alias*, or None if not defined."""
    return _load_aliases().get(alias)


def list_aliases() -> Dict[str, str]:
    """Return all alias → profile_name mappings."""
    return dict(_load_aliases())


def aliases_for_profile(profile_name: str) -> list[str]:
    """Return every alias that points to *profile_name*."""
    return [a for a, p in _load_aliases().items() if p == profile_name]

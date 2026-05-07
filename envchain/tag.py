"""Tag profiles with arbitrary labels for grouping and filtering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envchain.store import _store_dir


class TagError(Exception):
    pass


_TAGS_FILE = "tags.json"


def _tags_path() -> Path:
    return _store_dir() / _TAGS_FILE


def _load_tags() -> Dict[str, List[str]]:
    path = _tags_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise TagError(f"Failed to read tags file: {exc}") from exc


def _save_tags(data: Dict[str, List[str]]) -> None:
    path = _tags_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise TagError(f"Failed to write tags file: {exc}") from exc


def add_tag(profile: str, tag: str) -> None:
    """Add *tag* to *profile*. No-op if the tag already exists."""
    data = _load_tags()
    tags = data.setdefault(profile, [])
    if tag not in tags:
        tags.append(tag)
        _save_tags(data)


def remove_tag(profile: str, tag: str) -> None:
    """Remove *tag* from *profile*. Raises TagError if tag not present."""
    data = _load_tags()
    tags = data.get(profile, [])
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found on profile '{profile}'.")
    tags.remove(tag)
    if not tags:
        data.pop(profile, None)
    else:
        data[profile] = tags
    _save_tags(data)


def get_tags(profile: str) -> List[str]:
    """Return all tags for *profile*, or empty list."""
    return list(_load_tags().get(profile, []))


def profiles_with_tag(tag: str) -> List[str]:
    """Return all profile names that carry *tag*."""
    return [p for p, tags in _load_tags().items() if tag in tags]


def clear_tags(profile: str) -> None:
    """Remove all tags from *profile*."""
    data = _load_tags()
    data.pop(profile, None)
    _save_tags(data)

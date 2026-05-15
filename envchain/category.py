"""Profile category management for envchain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envchain.store import _store_dir


class CategoryError(Exception):
    """Raised when a category operation fails."""


def _categories_path() -> Path:
    return _store_dir() / "categories.json"


def _load_categories() -> Dict[str, str]:
    path = _categories_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_categories(data: Dict[str, str]) -> None:
    path = _categories_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def set_category(profile: str, category: str) -> str:
    """Assign a category to a profile."""
    if not profile:
        raise CategoryError("Profile name must not be empty.")
    if not category:
        raise CategoryError("Category must not be empty.")
    category = category.strip()
    if not category:
        raise CategoryError("Category must not be blank.")
    data = _load_categories()
    data[profile] = category
    _save_categories(data)
    return category


def get_category(profile: str) -> Optional[str]:
    """Return the category assigned to a profile, or None."""
    return _load_categories().get(profile)


def remove_category(profile: str) -> bool:
    """Remove the category for a profile. Returns True if it existed."""
    data = _load_categories()
    if profile not in data:
        return False
    del data[profile]
    _save_categories(data)
    return True


def list_categories() -> Dict[str, str]:
    """Return a mapping of profile -> category, sorted by profile name."""
    data = _load_categories()
    return dict(sorted(data.items()))


def find_by_category(category: str, case_sensitive: bool = False) -> List[str]:
    """Return profiles that belong to the given category."""
    data = _load_categories()
    needle = category if case_sensitive else category.lower()
    return sorted(
        profile
        for profile, cat in data.items()
        if (cat if case_sensitive else cat.lower()) == needle
    )

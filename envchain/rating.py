"""Profile rating/scoring module for envchain."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class RatingError(Exception):
    pass


MIN_RATING = 1
MAX_RATING = 5


def _ratings_path() -> Path:
    return _store_dir() / "ratings.json"


def _load_ratings() -> dict:
    p = _ratings_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_ratings(data: dict) -> None:
    _ratings_path().write_text(json.dumps(data, indent=2))


def set_rating(profile: str, rating: int) -> int:
    """Set an integer star rating (1–5) for a profile."""
    if not profile:
        raise RatingError("Profile name must not be empty.")
    if not isinstance(rating, int) or not (MIN_RATING <= rating <= MAX_RATING):
        raise RatingError(f"Rating must be an integer between {MIN_RATING} and {MAX_RATING}.")
    data = _load_ratings()
    data[profile] = rating
    _save_ratings(data)
    return rating


def get_rating(profile: str) -> Optional[int]:
    """Return the rating for *profile*, or None if not set."""
    return _load_ratings().get(profile)


def clear_rating(profile: str) -> bool:
    """Remove the rating for *profile*. Returns True if it existed."""
    data = _load_ratings()
    if profile in data:
        del data[profile]
        _save_ratings(data)
        return True
    return False


def list_ratings() -> dict[str, int]:
    """Return all profile ratings sorted alphabetically by profile name."""
    return dict(sorted(_load_ratings().items()))

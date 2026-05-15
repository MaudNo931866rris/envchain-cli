"""Human-readable labels and descriptions for profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class LabelError(Exception):
    pass


def _labels_path() -> Path:
    return _store_dir() / "labels.json"


def _load_labels() -> dict:
    p = _labels_path()
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_labels(data: dict) -> None:
    p = _labels_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_label(profile: str, label: str, description: str = "") -> None:
    """Assign a human-readable label and optional description to a profile."""
    if not profile:
        raise LabelError("Profile name must not be empty.")
    if not label:
        raise LabelError("Label must not be empty.")
    data = _load_labels()
    data[profile] = {"label": label, "description": description}
    _save_labels(data)


def get_label(profile: str) -> Optional[dict]:
    """Return label info for a profile, or None if not set."""
    return _load_labels().get(profile)


def remove_label(profile: str) -> None:
    """Remove label entry for a profile."""
    data = _load_labels()
    if profile not in data:
        raise LabelError(f"No label found for profile '{profile}'.")
    del data[profile]
    _save_labels(data)


def list_labels() -> dict:
    """Return all profile label entries."""
    return dict(_load_labels())


def find_by_label(query: str, case_sensitive: bool = False) -> list[dict]:
    """Return profiles whose label or description contains the query string."""
    data = _load_labels()
    results = []
    q = query if case_sensitive else query.lower()
    for profile, info in data.items():
        label = info.get("label", "")
        desc = info.get("description", "")
        haystack = f"{label} {desc}" if case_sensitive else f"{label} {desc}".lower()
        if q in haystack:
            results.append({"profile": profile, **info})
    return results

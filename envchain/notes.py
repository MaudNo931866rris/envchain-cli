"""Per-profile and per-variable plaintext notes/annotations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envchain.store import _store_dir


class NoteError(Exception):
    pass


def _notes_path() -> Path:
    return _store_dir() / "notes.json"


def _load_notes() -> Dict[str, Dict[str, str]]:
    p = _notes_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise NoteError(f"Corrupt notes file: {exc}") from exc


def _save_notes(data: Dict[str, Dict[str, str]]) -> None:
    _notes_path().write_text(json.dumps(data, indent=2))


def set_note(profile: str, note: str, *, key: Optional[str] = None) -> None:
    """Attach a note to *profile* or to a specific *key* within it."""
    if not profile:
        raise NoteError("profile name must not be empty")
    data = _load_notes()
    entry = data.setdefault(profile, {})
    slot = key if key else "__profile__"
    entry[slot] = note
    _save_notes(data)


def get_note(profile: str, *, key: Optional[str] = None) -> Optional[str]:
    """Return the note for *profile* (or *key* within it), or None."""
    data = _load_notes()
    entry = data.get(profile, {})
    slot = key if key else "__profile__"
    return entry.get(slot)


def remove_note(profile: str, *, key: Optional[str] = None) -> None:
    """Remove a note.  Silently succeeds if no note exists."""
    data = _load_notes()
    entry = data.get(profile, {})
    slot = key if key else "__profile__"
    entry.pop(slot, None)
    if not entry:
        data.pop(profile, None)
    else:
        data[profile] = entry
    _save_notes(data)


def list_notes(profile: str) -> Dict[str, str]:
    """Return all notes for *profile* as {slot: note}."""
    return dict(_load_notes().get(profile, {}))


def clear_notes(profile: str) -> None:
    """Remove every note attached to *profile*."""
    data = _load_notes()
    data.pop(profile, None)
    _save_notes(data)

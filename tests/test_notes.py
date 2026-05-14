"""Tests for envchain.notes and envchain.cli_notes."""

from __future__ import annotations

import argparse
import pytest

from envchain.notes import (
    NoteError,
    clear_notes,
    get_note,
    list_notes,
    remove_note,
    set_note,
)
from envchain.cli_notes import (
    cmd_note_get,
    cmd_note_list,
    cmd_note_remove,
    cmd_note_set,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    import envchain.store as store_mod
    import envchain.notes as notes_mod

    monkeypatch.setattr(store_mod, "_store_dir", lambda: tmp_path)
    monkeypatch.setattr(notes_mod, "_notes_path", lambda: tmp_path / "notes.json")
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "myproj", "key": "", "note": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- unit tests for notes module ---

def test_set_and_get_profile_note():
    set_note("proj", "main project")
    assert get_note("proj") == "main project"


def test_set_and_get_key_note():
    set_note("proj", "the api token", key="API_KEY")
    assert get_note("proj", key="API_KEY") == "the api token"


def test_get_missing_note_returns_none():
    assert get_note("ghost") is None
    assert get_note("ghost", key="X") is None


def test_remove_note_makes_it_gone():
    set_note("proj", "hello")
    remove_note("proj")
    assert get_note("proj") is None


def test_remove_missing_note_is_silent():
    remove_note("nonexistent")
    remove_note("nonexistent", key="K")


def test_list_notes_returns_all_slots():
    set_note("proj", "profile note")
    set_note("proj", "key note", key="DB_URL")
    notes = list_notes("proj")
    assert notes["__profile__"] == "profile note"
    assert notes["DB_URL"] == "key note"


def test_clear_notes_removes_all():
    set_note("proj", "a")
    set_note("proj", "b", key="X")
    clear_notes("proj")
    assert list_notes("proj") == {}


def test_set_note_empty_profile_raises():
    with pytest.raises(NoteError):
        set_note("", "oops")


# --- CLI command tests ---

def test_cmd_note_set_returns_zero():
    assert cmd_note_set(_args(note="test note")) == 0


def test_cmd_note_set_persists():
    cmd_note_set(_args(note="persisted"))
    assert get_note("myproj") == "persisted"


def test_cmd_note_get_returns_zero_when_found(capsys):
    set_note("myproj", "hello world")
    rc = cmd_note_get(_args())
    assert rc == 0
    assert "hello world" in capsys.readouterr().out


def test_cmd_note_get_returns_one_when_missing():
    assert cmd_note_get(_args()) == 1


def test_cmd_note_remove_returns_zero():
    set_note("myproj", "bye")
    assert cmd_note_remove(_args()) == 0


def test_cmd_note_list_returns_zero_empty(capsys):
    rc = cmd_note_list(_args())
    assert rc == 0


def test_cmd_note_list_shows_notes(capsys):
    set_note("myproj", "top-level")
    set_note("myproj", "secret token", key="TOKEN")
    cmd_note_list(_args())
    out = capsys.readouterr().out
    assert "top-level" in out
    assert "TOKEN" in out
    assert "secret token" in out

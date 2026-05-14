"""CLI commands for managing profile and variable notes."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envchain.notes import (
    NoteError,
    clear_notes,
    get_note,
    list_notes,
    remove_note,
    set_note,
)


def cmd_note_set(args: argparse.Namespace) -> int:
    """Set a note on a profile or a specific key."""
    try:
        set_note(args.profile, args.note, key=args.key or None)
    except NoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    target = f"{args.profile}:{args.key}" if args.key else args.profile
    print(f"Note set for '{target}'.")
    return 0


def cmd_note_get(args: argparse.Namespace) -> int:
    """Print the note for a profile or key."""
    try:
        note = get_note(args.profile, key=args.key or None)
    except NoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if note is None:
        target = f"{args.profile}:{args.key}" if args.key else args.profile
        print(f"No note found for '{target}'.", file=sys.stderr)
        return 1
    print(note)
    return 0


def cmd_note_remove(args: argparse.Namespace) -> int:
    """Remove a note from a profile or key."""
    try:
        remove_note(args.profile, key=args.key or None)
    except NoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    target = f"{args.profile}:{args.key}" if args.key else args.profile
    print(f"Note removed for '{target}'.")
    return 0


def cmd_note_list(args: argparse.Namespace) -> int:
    """List all notes attached to a profile."""
    try:
        notes = list_notes(args.profile)
    except NoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not notes:
        print(f"No notes for profile '{args.profile}'.")
        return 0
    for slot, text in sorted(notes.items()):
        label = "(profile)" if slot == "__profile__" else slot
        print(f"  {label}: {text}")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_set = subparsers.add_parser("note-set", help="Attach a note to a profile or key")
    p_set.add_argument("profile")
    p_set.add_argument("note")
    p_set.add_argument("--key", default="", help="Variable key to annotate")
    p_set.set_defaults(func=cmd_note_set)

    p_get = subparsers.add_parser("note-get", help="Print a note")
    p_get.add_argument("profile")
    p_get.add_argument("--key", default="", help="Variable key")
    p_get.set_defaults(func=cmd_note_get)

    p_rm = subparsers.add_parser("note-remove", help="Remove a note")
    p_rm.add_argument("profile")
    p_rm.add_argument("--key", default="", help="Variable key")
    p_rm.set_defaults(func=cmd_note_remove)

    p_ls = subparsers.add_parser("note-list", help="List all notes for a profile")
    p_ls.add_argument("profile")
    p_ls.set_defaults(func=cmd_note_list)

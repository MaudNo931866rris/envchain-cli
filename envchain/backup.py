"""Backup and restore all profiles to/from a single encrypted archive."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from envchain.store import _store_dir, _profile_path, list_profiles
from envchain.crypto import encrypt_profile, decrypt_profile


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def _backup_dir() -> Path:
    d = _store_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _backup_path(label: str) -> Path:
    return _backup_dir() / f"{label}.ecbak"


def create_backup(label: str, passphrase: str) -> Path:
    """Encrypt all profiles into a single backup archive file.

    Each profile is read as raw bytes (already encrypted at rest) and bundled
    into a JSON manifest which is then re-encrypted with *passphrase*.

    Returns the path to the created backup file.
    """
    dest = _backup_path(label)
    if dest.exists():
        raise BackupError(f"Backup '{label}' already exists.")

    names = list_profiles()
    if not names:
        raise BackupError("No profiles found to back up.")

    bundle: Dict[str, str] = {}
    for name in names:
        path = _profile_path(name)
        bundle[name] = path.read_text(encoding="utf-8")

    plaintext = json.dumps(bundle)
    ciphertext = encrypt_profile(plaintext, passphrase)
    dest.write_text(ciphertext, encoding="utf-8")
    return dest


def restore_backup(label: str, passphrase: str, overwrite: bool = False) -> List[str]:
    """Decrypt a backup archive and restore all profiles.

    Returns a list of restored profile names.
    Raises BackupError if the backup does not exist or decryption fails.
    """
    src = _backup_path(label)
    if not src.exists():
        raise BackupError(f"Backup '{label}' not found.")

    try:
        plaintext = decrypt_profile(src.read_text(encoding="utf-8"), passphrase)
    except Exception as exc:
        raise BackupError(f"Failed to decrypt backup: {exc}") from exc

    bundle: Dict[str, str] = json.loads(plaintext)
    restored: List[str] = []
    for name, raw in bundle.items():
        path = _profile_path(name)
        if path.exists() and not overwrite:
            continue
        path.write_text(raw, encoding="utf-8")
        restored.append(name)
    return restored


def list_backups() -> List[str]:
    """Return labels of all available backups."""
    return sorted(
        p.stem for p in _backup_dir().glob("*.ecbak")
    )


def delete_backup(label: str) -> None:
    """Delete a backup archive by label."""
    path = _backup_path(label)
    if not path.exists():
        raise BackupError(f"Backup '{label}' not found.")
    path.unlink()

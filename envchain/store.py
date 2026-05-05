"""Profile store: load, save, list, and delete encrypted profiles on disk."""

import json
import os
from pathlib import Path
from typing import Dict, List

from envchain.crypto import decrypt_profile, encrypt_profile

DEFAULT_STORE_DIR = Path.home() / ".envchain" / "profiles"


def _store_dir() -> Path:
    """Return the profile store directory, honouring ENVCHAIN_DIR env var."""
    custom = os.environ.get("ENVCHAIN_DIR")
    return Path(custom) if custom else DEFAULT_STORE_DIR


def _profile_path(name: str) -> Path:
    return _store_dir() / f"{name}.enc"


def save_profile(name: str, variables: Dict[str, str], passphrase: str) -> None:
    """Encrypt *variables* and write them to the profile store."""
    store_dir = _store_dir()
    store_dir.mkdir(parents=True, exist_ok=True)
    plaintext = json.dumps(variables)
    ciphertext = encrypt_profile(plaintext, passphrase)
    _profile_path(name).write_text(ciphertext)


def load_profile(name: str, passphrase: str) -> Dict[str, str]:
    """Decrypt and return the variables stored under *name*.

    Raises FileNotFoundError if the profile does not exist.
    Raises ValueError (from crypto layer) on wrong passphrase / tampered data.
    """
    path = _profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found.")
    ciphertext = path.read_text()
    plaintext = decrypt_profile(ciphertext, passphrase)
    return json.loads(plaintext)


def delete_profile(name: str) -> None:
    """Remove a profile from the store. Raises FileNotFoundError if absent."""
    path = _profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found.")
    path.unlink()


def list_profiles() -> List[str]:
    """Return sorted list of profile names available in the store."""
    store_dir = _store_dir()
    if not store_dir.exists():
        return []
    return sorted(p.stem for p in store_dir.glob("*.enc"))

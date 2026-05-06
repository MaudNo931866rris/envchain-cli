"""Export and import profiles as portable encrypted bundles."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from envchain.crypto import decrypt_profile, encrypt_profile
from envchain.store import load_profile, save_profile


class ExportError(Exception):
    """Raised when export/import fails."""


BUNDLE_VERSION = 1


def export_profile(profile_name: str, passphrase: str, out_path: Path) -> None:
    """Export an encrypted profile to a portable JSON bundle file.

    The bundle contains the profile name, bundle version, and the
    re-encrypted ciphertext so it can be shared and imported elsewhere.
    """
    env_vars = load_profile(profile_name, passphrase)

    plaintext = json.dumps(env_vars)
    ciphertext = encrypt_profile(plaintext, passphrase)

    bundle = {
        "version": BUNDLE_VERSION,
        "profile": profile_name,
        "data": base64.b64encode(ciphertext.encode()).decode(),
    }

    out_path.write_text(json.dumps(bundle, indent=2))


def import_profile(
    bundle_path: Path,
    passphrase: str,
    *,
    overwrite: bool = False,
    rename: str | None = None,
) -> str:
    """Import a profile bundle, returning the profile name written.

    Args:
        bundle_path: Path to the .envbundle JSON file.
        passphrase: Passphrase used to decrypt the bundle.
        overwrite: If False (default), raise ExportError if profile exists.
        rename: Optional new name for the imported profile.

    Returns:
        The name of the profile that was saved.
    """
    try:
        bundle = json.loads(bundle_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"Cannot read bundle: {exc}") from exc

    if bundle.get("version") != BUNDLE_VERSION:
        raise ExportError(
            f"Unsupported bundle version: {bundle.get('version')}"
        )

    raw_data = base64.b64decode(bundle["data"]).decode()
    plaintext = decrypt_profile(raw_data, passphrase)
    env_vars: dict[str, str] = json.loads(plaintext)

    profile_name: str = rename or bundle["profile"]

    from envchain.store import _profile_path  # avoid circular at module level

    if not overwrite and _profile_path(profile_name).exists():
        raise ExportError(
            f"Profile '{profile_name}' already exists. Use overwrite=True to replace it."
        )

    save_profile(profile_name, env_vars, passphrase)
    return profile_name

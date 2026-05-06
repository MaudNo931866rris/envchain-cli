"""CLI sub-commands for profile export and import.

Integrate into the main CLI with::

    from envchain.cli_export import cmd_export, cmd_import
"""

from __future__ import annotations

from pathlib import Path

from envchain.export import ExportError, export_profile, import_profile


def cmd_export(
    profile_name: str,
    passphrase: str,
    output: str | None = None,
) -> int:
    """Export a profile to a .envbundle file.

    Args:
        profile_name: Name of the profile to export.
        passphrase: Passphrase for decrypting the stored profile.
        output: Destination file path. Defaults to '<profile>.envbundle'.

    Returns:
        0 on success, 1 on error.
    """
    out_path = Path(output) if output else Path(f"{profile_name}.envbundle")
    try:
        export_profile(profile_name, passphrase, out_path)
        print(f"Exported profile '{profile_name}' → {out_path}")
        return 0
    except FileNotFoundError:
        print(f"Error: profile '{profile_name}' not found.")
        return 1
    except ExportError as exc:
        print(f"Export error: {exc}")
        return 1


def cmd_import(
    bundle_path: str,
    passphrase: str,
    *,
    overwrite: bool = False,
    rename: str | None = None,
) -> int:
    """Import a profile from a .envbundle file.

    Args:
        bundle_path: Path to the bundle file.
        passphrase: Passphrase to decrypt the bundle.
        overwrite: Replace an existing profile with the same name.
        rename: Save the profile under a different name.

    Returns:
        0 on success, 1 on error.
    """
    try:
        name = import_profile(
            Path(bundle_path),
            passphrase,
            overwrite=overwrite,
            rename=rename,
        )
        print(f"Imported profile '{name}' from {bundle_path}")
        return 0
    except ExportError as exc:
        print(f"Import error: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to import: {exc}")
        return 1

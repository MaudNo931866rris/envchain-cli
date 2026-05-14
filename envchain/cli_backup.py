"""CLI commands for backup and restore of all profiles."""

from __future__ import annotations

import argparse
import getpass
import sys
from typing import List

from envchain.backup import (
    BackupError,
    create_backup,
    restore_backup,
    list_backups,
    delete_backup,
)


def _prompt_passphrase(prompt: str = "Passphrase: ") -> str:
    return getpass.getpass(prompt)


def cmd_backup_create(args: argparse.Namespace) -> int:
    passphrase = args.passphrase or _prompt_passphrase("Backup passphrase: ")
    try:
        path = create_backup(args.label, passphrase)
        print(f"Backup '{args.label}' created at {path}")
        return 0
    except BackupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_backup_restore(args: argparse.Namespace) -> int:
    passphrase = args.passphrase or _prompt_passphrase("Backup passphrase: ")
    try:
        restored = restore_backup(args.label, passphrase, overwrite=args.overwrite)
        if restored:
            print(f"Restored profiles: {', '.join(restored)}")
        else:
            print("No profiles restored (all already exist; use --overwrite to force).")
        return 0
    except BackupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_backup_list(args: argparse.Namespace) -> int:  # noqa: ARG001
    labels = list_backups()
    if not labels:
        print("No backups found.")
    else:
        for label in labels:
            print(label)
    return 0


def cmd_backup_delete(args: argparse.Namespace) -> int:
    try:
        delete_backup(args.label)
        print(f"Backup '{args.label}' deleted.")
        return 0
    except BackupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("backup", help="Backup and restore all profiles")
    sub = p.add_subparsers(dest="backup_cmd", required=True)

    pc = sub.add_parser("create", help="Create a new backup")
    pc.add_argument("label", help="Backup label")
    pc.add_argument("--passphrase", default=None)
    pc.set_defaults(func=cmd_backup_create)

    pr = sub.add_parser("restore", help="Restore profiles from a backup")
    pr.add_argument("label", help="Backup label")
    pr.add_argument("--passphrase", default=None)
    pr.add_argument("--overwrite", action="store_true", default=False)
    pr.set_defaults(func=cmd_backup_restore)

    pl = sub.add_parser("list", help="List available backups")
    pl.set_defaults(func=cmd_backup_list)

    pd = sub.add_parser("delete", help="Delete a backup")
    pd.add_argument("label", help="Backup label")
    pd.set_defaults(func=cmd_backup_delete)

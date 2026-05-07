"""CLI commands for profile snapshot management."""

from __future__ import annotations

import argparse
import sys
from getpass import getpass
from typing import List

from envchain.profile import load
from envchain.snapshot import SnapshotError, delete_snapshot, list_snapshots, load_snapshot, save_snapshot
from envchain.audit import record_event


def _prompt_passphrase(profile: str) -> str:
    return getpass(f"Passphrase for '{profile}': ")


def cmd_snapshot_save(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    passphrase = _prompt_passphrase(args.profile)
    try:
        prof = load(args.profile, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=err)
        return 1
    try:
        snap = save_snapshot(args.profile, prof.as_env_dict(), args.label)
    except SnapshotError as exc:
        print(f"error: {exc}", file=err)
        return 1
    record_event("snapshot_save", args.profile, detail=args.label)
    print(f"Snapshot '{snap.label}' saved for profile '{args.profile}' at {snap.created_at}.", file=out)
    return 0


def cmd_snapshot_restore(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        snap = load_snapshot(args.profile, args.label)
    except SnapshotError as exc:
        print(f"error: {exc}", file=err)
        return 1
    passphrase = _prompt_passphrase(args.profile)
    try:
        prof = load(args.profile, passphrase)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=err)
        return 1
    for key, value in snap.variables.items():
        prof.set_var(key, value)
    prof.save(passphrase)
    record_event("snapshot_restore", args.profile, detail=args.label)
    print(f"Profile '{args.profile}' restored from snapshot '{args.label}'.", file=out)
    return 0


def cmd_snapshot_list(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    labels = list_snapshots(args.profile)
    if not labels:
        print(f"No snapshots for profile '{args.profile}'.", file=out)
        return 0
    for label in labels:
        print(label, file=out)
    return 0


def cmd_snapshot_delete(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    try:
        delete_snapshot(args.profile, args.label)
    except SnapshotError as exc:
        print(f"error: {exc}", file=err)
        return 1
    record_event("snapshot_delete", args.profile, detail=args.label)
    print(f"Snapshot '{args.label}' deleted.", file=out)
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("snapshot", help="Manage profile snapshots")
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    ps = sub.add_parser("save", help="Save a snapshot")
    ps.add_argument("profile"); ps.add_argument("label")
    ps.set_defaults(func=cmd_snapshot_save)

    pr = sub.add_parser("restore", help="Restore a snapshot")
    pr.add_argument("profile"); pr.add_argument("label")
    pr.set_defaults(func=cmd_snapshot_restore)

    pl = sub.add_parser("list", help="List snapshots")
    pl.add_argument("profile")
    pl.set_defaults(func=cmd_snapshot_list)

    pd = sub.add_parser("delete", help="Delete a snapshot")
    pd.add_argument("profile"); pd.add_argument("label")
    pd.set_defaults(func=cmd_snapshot_delete)

"""CLI commands for merging profiles."""

from __future__ import annotations

import argparse
import getpass
import sys
from typing import List

from envchain.merge import merge_profiles, MergeError
from envchain.audit import record_event


def _prompt_passphrase(prompt: str) -> str:
    return getpass.getpass(prompt)


def cmd_merge(args: argparse.Namespace) -> int:
    """Merge one or more source profiles into a destination profile.

    Returns 0 on success, 1 on error.
    """
    src_passphrase = _prompt_passphrase("Source passphrase: ")

    if args.same_passphrase:
        dst_passphrase = src_passphrase
    else:
        dst_passphrase = _prompt_passphrase(f"Destination passphrase ('{args.destination}'): ")

    try:
        result = merge_profiles(
            source_names=args.sources,
            destination_name=args.destination,
            src_passphrase=src_passphrase,
            dst_passphrase=dst_passphrase,
            overwrite=args.overwrite,
        )
    except MergeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    total = len(result.merged_keys) + len(result.overwritten_keys)
    print(
        f"Merged {total} key(s) into '{result.destination}' "
        f"({len(result.skipped_keys)} skipped)."
    )
    if result.merged_keys:
        print("  added:      " + ", ".join(sorted(result.merged_keys)))
    if result.overwritten_keys:
        print("  overwritten: " + ", ".join(sorted(result.overwritten_keys)))
    if result.skipped_keys:
        print("  skipped:    " + ", ".join(sorted(result.skipped_keys)))

    record_event(
        "merge",
        profile=result.destination,
        detail=f"sources={','.join(args.sources)} added={len(result.merged_keys)} "
               f"overwritten={len(result.overwritten_keys)} skipped={len(result.skipped_keys)}",
    )
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "merge",
        help="Merge variables from source profiles into a destination profile.",
    )
    parser.add_argument("destination", help="Profile that receives merged variables.")
    parser.add_argument("sources", nargs="+", help="One or more source profile names.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in the destination.",
    )
    parser.add_argument(
        "--same-passphrase",
        action="store_true",
        default=False,
        help="Use the same passphrase for source and destination profiles.",
    )
    parser.set_defaults(func=cmd_merge)

"""CLI commands for searching across envchain profiles."""

from __future__ import annotations

import getpass
import sys
from typing import List

from envchain.search import search_profiles
from envchain.store import list_profiles


def cmd_search(args) -> int:  # noqa: ANN001
    """Search profiles for a matching key (or value).

    Usage: envchain search <query> [--values] [--show] [--profiles p1,p2]
    """
    query: str = args.query
    search_values: bool = getattr(args, "values", False)
    show_values: bool = getattr(args, "show", False)
    case_sensitive: bool = getattr(args, "case_sensitive", False)
    profiles_arg: str = getattr(args, "profiles", "") or ""

    if profiles_arg:
        profile_names: List[str] = [p.strip() for p in profiles_arg.split(",") if p.strip()]
    else:
        profile_names = list_profiles()

    if not profile_names:
        print("No profiles found.", file=sys.stderr)
        return 1

    passphrase = getpass.getpass("Passphrase: ")

    results = search_profiles(
        profile_names,
        passphrase,
        query,
        search_values=search_values,
        show_values=show_values,
        case_sensitive=case_sensitive,
    )

    if not results:
        print(f"No matches found for '{query}'.")
        return 0

    current_profile = None
    for r in results:
        if r.profile_name != current_profile:
            current_profile = r.profile_name
            print(f"\n[{current_profile}]")
        if r.value_preview is not None:
            print(f"  {r.key} = {r.value_preview}")
        else:
            print(f"  {r.key}")

    print()
    return 0

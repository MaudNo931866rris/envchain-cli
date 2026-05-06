"""Search across profiles for environment variable keys or values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.profile import load


@dataclass
class SearchResult:
    profile_name: str
    key: str
    value_preview: Optional[str] = None  # None means value hidden

    def as_dict(self) -> dict:
        return {
            "profile": self.profile_name,
            "key": self.key,
            "value_preview": self.value_preview,
        }


def search_profiles(
    profile_names: List[str],
    passphrase: str,
    query: str,
    *,
    search_values: bool = False,
    show_values: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Search for *query* across the given profiles.

    Args:
        profile_names: Profiles to search through.
        passphrase: Passphrase used to decrypt each profile.
        query: Substring to search for.
        search_values: Also search inside variable values.
        show_values: Include a (possibly truncated) value preview in results.
        case_sensitive: Perform a case-sensitive match.

    Returns:
        List of :class:`SearchResult` objects ordered by profile then key.
    """
    needle = query if case_sensitive else query.lower()
    results: List[SearchResult] = []

    for name in profile_names:
        try:
            profile = load(name, passphrase)
        except Exception:
            # Skip profiles that cannot be decrypted or don't exist.
            continue

        env = profile.as_env_dict()
        for key in sorted(env):
            hay_key = key if case_sensitive else key.lower()
            hay_val = env[key] if case_sensitive else env[key].lower()

            matched = needle in hay_key or (search_values and needle in hay_val)
            if matched:
                preview: Optional[str] = None
                if show_values:
                    raw = env[key]
                    preview = raw[:40] + "..." if len(raw) > 40 else raw
                results.append(SearchResult(profile_name=name, key=key, value_preview=preview))

    return results

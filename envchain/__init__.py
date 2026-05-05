"""envchain — Manage and inject environment variable sets per project context."""

from envchain.profile import Profile
from envchain.store import (
    delete_profile,
    list_profiles,
    load_profile,
    save_profile,
)

__all__ = [
    "Profile",
    "delete_profile",
    "list_profiles",
    "load_profile",
    "save_profile",
]

__version__ = "0.1.0"

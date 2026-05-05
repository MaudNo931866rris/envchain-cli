"""High-level Profile model wrapping the store layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envchain import store


@dataclass
class Profile:
    """Represents a named set of environment variables."""

    name: str
    variables: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def save(self, passphrase: str) -> None:
        """Persist this profile to the encrypted store."""
        store.save_profile(self.name, self.variables, passphrase)

    def delete(self, passphrase: str) -> None:  # noqa: ARG002  (passphrase unused but kept for API symmetry)
        """Remove this profile from the store."""
        store.delete_profile(self.name)

    # ------------------------------------------------------------------
    # Variable management
    # ------------------------------------------------------------------

    def set_var(self, key: str, value: str) -> None:
        """Add or update a variable in the profile."""
        self.variables[key] = value

    def unset_var(self, key: str) -> None:
        """Remove a variable; raises KeyError if not present."""
        if key not in self.variables:
            raise KeyError(f"Variable '{key}' not found in profile '{self.name}'.")
        del self.variables[key]

    def as_env_dict(self) -> Dict[str, str]:
        """Return a copy of the variables suitable for os.environ injection."""
        return dict(self.variables)

    # ------------------------------------------------------------------
    # Class-level factory methods
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, name: str, passphrase: str) -> "Profile":
        """Load an existing profile from the store."""
        variables = store.load_profile(name, passphrase)
        return cls(name=name, variables=variables)

    @classmethod
    def list_all(cls) -> List[str]:
        """Return names of all stored profiles."""
        return store.list_profiles()

"""Profile dependency tracking — declare and resolve load-order dependencies between profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envchain.store import _store_dir


class DependencyError(Exception):
    """Raised when dependency operations fail."""


def _deps_path() -> Path:
    return _store_dir() / "dependencies.json"


def _load_deps() -> Dict[str, List[str]]:
    p = _deps_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_deps(data: Dict[str, List[str]]) -> None:
    _deps_path().write_text(json.dumps(data, indent=2))


def add_dependency(profile: str, depends_on: str) -> None:
    """Declare that *profile* depends on *depends_on*."""
    if not profile:
        raise DependencyError("profile name must not be empty")
    if not depends_on:
        raise DependencyError("dependency name must not be empty")
    if profile == depends_on:
        raise DependencyError("a profile cannot depend on itself")
    data = _load_deps()
    deps = data.setdefault(profile, [])
    if depends_on not in deps:
        deps.append(depends_on)
    _save_deps(data)


def remove_dependency(profile: str, depends_on: str) -> None:
    """Remove a declared dependency."""
    data = _load_deps()
    deps = data.get(profile, [])
    if depends_on not in deps:
        raise DependencyError(f"{profile!r} does not depend on {depends_on!r}")
    deps.remove(depends_on)
    if not deps:
        data.pop(profile)
    _save_deps(data)


def get_dependencies(profile: str) -> List[str]:
    """Return direct dependencies of *profile*."""
    return list(_load_deps().get(profile, []))


def resolve_order(profile: str) -> List[str]:
    """Return a topologically sorted load order for *profile* and its transitive deps.

    Raises DependencyError on circular dependencies.
    """
    data = _load_deps()
    visited: List[str] = []
    visiting: set = set()

    def _visit(name: str) -> None:
        if name in visiting:
            raise DependencyError(f"circular dependency detected involving {name!r}")
        if name in visited:
            return
        visiting.add(name)
        for dep in data.get(name, []):
            _visit(dep)
        visiting.discard(name)
        visited.append(name)

    _visit(profile)
    return visited


def list_all_dependencies() -> Dict[str, List[str]]:
    """Return the full dependency map."""
    return dict(_load_deps())

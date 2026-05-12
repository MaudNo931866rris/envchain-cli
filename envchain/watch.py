"""Watch a profile for changes and re-run a command when vars are updated."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from envchain.store import _profile_path
from envchain.profile import load


class WatchError(Exception):
    """Raised when watch encounters an unrecoverable error."""


@dataclass
class WatchEvent:
    profile: str
    changed_at: float
    previous_mtime: float
    current_mtime: float


def _get_mtime(profile: str) -> Optional[float]:
    """Return the modification time of the profile file, or None if missing."""
    path = _profile_path(profile)
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return None


def watch_profile(
    profile: str,
    passphrase: str,
    command: list[str],
    interval: float = 1.0,
    max_cycles: Optional[int] = None,
    on_change: Optional[Callable[[WatchEvent], None]] = None,
) -> None:
    """Poll *profile* every *interval* seconds and re-run *command* on change.

    Args:
        profile:    Profile name to watch.
        passphrase: Passphrase used to decrypt the profile for env injection.
        command:    Command + args to execute on each detected change.
        interval:   Polling interval in seconds (default 1.0).
        max_cycles: Stop after this many poll cycles (None = run forever).
        on_change:  Optional callback invoked with a WatchEvent on each change.

    Raises:
        WatchError: If the profile does not exist at startup.
    """
    if _get_mtime(profile) is None:
        raise WatchError(f"Profile '{profile}' not found.")

    last_mtime = _get_mtime(profile)
    cycles = 0

    while max_cycles is None or cycles < max_cycles:
        time.sleep(interval)
        current_mtime = _get_mtime(profile)

        if current_mtime is None:
            raise WatchError(f"Profile '{profile}' was deleted while watching.")

        if current_mtime != last_mtime:
            event = WatchEvent(
                profile=profile,
                changed_at=time.time(),
                previous_mtime=last_mtime,
                current_mtime=current_mtime,
            )
            if on_change:
                on_change(event)

            p = load(profile, passphrase)
            env = {**os.environ, **p.as_env_dict()}
            subprocess.run(command, env=env)  # noqa: S603

            last_mtime = current_mtime

        cycles += 1

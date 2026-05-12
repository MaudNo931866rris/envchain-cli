"""Tests for envchain.watch."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envchain.profile import Profile, save
from envchain.watch import WatchError, WatchEvent, watch_profile

PROFILE = "watch-test"
PASS = "WatchPass1!"


@pytest.fixture()
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    return tmp_path


def _seed(isolated_store):
    p = Profile(name=PROFILE, vars={"KEY": "value1"})
    save(p, PASS)
    return p


# ---------------------------------------------------------------------------
# watch_profile raises when profile is missing
# ---------------------------------------------------------------------------

def test_watch_missing_profile_raises(isolated_store):
    with pytest.raises(WatchError, match="not found"):
        watch_profile(
            profile="no-such-profile",
            passphrase=PASS,
            command=["echo", "hi"],
            max_cycles=0,
        )


# ---------------------------------------------------------------------------
# watch_profile exits cleanly after max_cycles with no change
# ---------------------------------------------------------------------------

def test_watch_no_change_does_not_call_subprocess(isolated_store):
    _seed(isolated_store)
    with patch("envchain.watch.time.sleep"), \
         patch("envchain.watch.subprocess.run") as mock_run:
        watch_profile(
            profile=PROFILE,
            passphrase=PASS,
            command=["echo", "hi"],
            interval=0.0,
            max_cycles=3,
        )
    mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# watch_profile calls subprocess and on_change when mtime changes
# ---------------------------------------------------------------------------

def test_watch_detects_change_and_runs_command(isolated_store):
    _seed(isolated_store)

    call_count = 0

    def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            # Simulate a profile update by re-saving with a new var
            p = Profile(name=PROFILE, vars={"KEY": "value2"})
            save(p, PASS)

    events: list[WatchEvent] = []

    with patch("envchain.watch.time.sleep", side_effect=fake_sleep), \
         patch("envchain.watch.subprocess.run") as mock_run:
        watch_profile(
            profile=PROFILE,
            passphrase=PASS,
            command=["echo", "changed"],
            interval=0.0,
            max_cycles=4,
            on_change=events.append,
        )

    assert len(events) == 1
    assert events[0].profile == PROFILE
    assert events[0].current_mtime > events[0].previous_mtime
    mock_run.assert_called_once()
    _env = mock_run.call_args.kwargs["env"]
    assert _env["KEY"] == "value2"


# ---------------------------------------------------------------------------
# watch_profile raises when profile disappears mid-watch
# ---------------------------------------------------------------------------

def test_watch_raises_if_profile_deleted_mid_watch(isolated_store):
    _seed(isolated_store)
    from envchain.store import delete_profile

    call_count = 0

    def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            delete_profile(PROFILE)

    with patch("envchain.watch.time.sleep", side_effect=fake_sleep):
        with pytest.raises(WatchError, match="deleted while watching"):
            watch_profile(
                profile=PROFILE,
                passphrase=PASS,
                command=["echo", "hi"],
                interval=0.0,
                max_cycles=3,
            )

"""Tests for envchain.pin module."""

from __future__ import annotations

import pytest

from envchain import pin as pin_mod
from envchain.pin import (
    PinError,
    clear_pin,
    has_pin,
    require_pin,
    set_pin,
    verify_pin,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_set_pin_creates_entry():
    set_pin("myproject", "1234")
    assert has_pin("myproject")


def test_has_pin_false_before_set():
    assert not has_pin("ghost")


def test_verify_pin_correct():
    set_pin("proj", "5678")
    assert verify_pin("proj", "5678") is True


def test_verify_pin_wrong():
    set_pin("proj", "5678")
    assert verify_pin("proj", "9999") is False


def test_verify_pin_no_pin_set_returns_true():
    # No PIN configured — any value passes
    assert verify_pin("nopinprof", "0000") is True


def test_require_pin_passes_on_correct():
    set_pin("secure", "4321")
    require_pin("secure", "4321")  # should not raise


def test_require_pin_raises_on_wrong():
    set_pin("secure", "4321")
    with pytest.raises(PinError, match="Incorrect PIN"):
        require_pin("secure", "0000")


def test_clear_pin_removes_entry():
    set_pin("temp", "1111")
    assert has_pin("temp")
    clear_pin("temp")
    assert not has_pin("temp")


def test_clear_pin_noop_if_not_set():
    clear_pin("nonexistent")  # should not raise


def test_set_pin_too_short_raises():
    with pytest.raises(PinError, match="4-8 numeric digits"):
        set_pin("proj", "12")


def test_set_pin_too_long_raises():
    with pytest.raises(PinError, match="4-8 numeric digits"):
        set_pin("proj", "123456789")


def test_set_pin_non_numeric_raises():
    with pytest.raises(PinError, match="4-8 numeric digits"):
        set_pin("proj", "abcd")


def test_pins_file_permissions(isolated_store):
    import stat

    set_pin("proj", "2468")
    pins_file = isolated_store / "pins.json"
    mode = stat.S_IMODE(pins_file.stat().st_mode)
    assert mode == 0o600


def test_multiple_profiles_independent():
    set_pin("alpha", "1234")
    set_pin("beta", "5678")
    assert verify_pin("alpha", "1234")
    assert verify_pin("beta", "5678")
    assert not verify_pin("alpha", "5678")

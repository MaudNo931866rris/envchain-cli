"""Tests for envchain.cli_rating."""
import argparse
import pytest

from envchain.cli_rating import (
    cmd_rating_set,
    cmd_rating_clear,
    cmd_rating_show,
    cmd_rating_list,
)
from envchain.rating import set_rating


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.rating._store_dir", lambda: tmp_path)
    yield tmp_path


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_rating_set_returns_zero():
    assert cmd_rating_set(_args(profile="proj", rating=4)) == 0


def test_cmd_rating_set_persists():
    from envchain.rating import get_rating
    cmd_rating_set(_args(profile="proj", rating=3))
    assert get_rating("proj") == 3


def test_cmd_rating_set_invalid_rating_returns_one():
    assert cmd_rating_set(_args(profile="proj", rating=10)) == 1


def test_cmd_rating_set_empty_profile_returns_one():
    assert cmd_rating_set(_args(profile="", rating=3)) == 1


def test_cmd_rating_clear_returns_zero_when_exists():
    set_rating("proj", 5)
    assert cmd_rating_clear(_args(profile="proj")) == 0


def test_cmd_rating_clear_returns_zero_when_missing():
    assert cmd_rating_clear(_args(profile="ghost")) == 0


def test_cmd_rating_show_returns_zero_when_set(capsys):
    set_rating("proj", 5)
    rc = cmd_rating_show(_args(profile="proj"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "★★★★★" in out


def test_cmd_rating_show_no_rating_message(capsys):
    cmd_rating_show(_args(profile="unknown"))
    out = capsys.readouterr().out
    assert "No rating" in out


def test_cmd_rating_list_returns_zero(capsys):
    set_rating("a", 1)
    set_rating("b", 2)
    rc = cmd_rating_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "a" in out and "b" in out


def test_cmd_rating_list_empty_message(capsys):
    cmd_rating_list(_args())
    out = capsys.readouterr().out
    assert "No ratings" in out

"""Tests for envchain.cli_quota."""

from __future__ import annotations

import argparse

import pytest

from envchain.cli_quota import (
    cmd_quota_clear,
    cmd_quota_list,
    cmd_quota_set,
    cmd_quota_show,
)
from envchain.quota import QuotaPolicy, set_quota


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("envchain.quota._store_dir", lambda: tmp_path)
    return tmp_path


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        profile="testproj",
        max_vars=100,
        max_value_bytes=4096,
        max_total_bytes=65536,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_quota_set_returns_zero(capsys):
    rc = cmd_quota_set(_args(max_vars=20))
    assert rc == 0
    out = capsys.readouterr().out
    assert "max_vars=20" in out


def test_cmd_quota_set_persists():
    from envchain.quota import get_quota
    cmd_quota_set(_args(max_vars=7, max_value_bytes=128, max_total_bytes=1024))
    policy = get_quota("testproj")
    assert policy.max_vars == 7
    assert policy.max_value_bytes == 128


def test_cmd_quota_clear_returns_zero(capsys):
    cmd_quota_set(_args())
    rc = cmd_quota_clear(_args())
    assert rc == 0
    assert "cleared" in capsys.readouterr().out


def test_cmd_quota_show_no_policy(capsys):
    rc = cmd_quota_show(_args())
    assert rc == 0
    assert "No quota" in capsys.readouterr().out


def test_cmd_quota_show_with_policy(capsys):
    set_quota("testproj", QuotaPolicy(max_vars=42))
    rc = cmd_quota_show(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "42" in out


def test_cmd_quota_list_empty(capsys):
    rc = cmd_quota_list(_args())
    assert rc == 0
    assert "No quota" in capsys.readouterr().out


def test_cmd_quota_list_shows_all(capsys):
    set_quota("alpha", QuotaPolicy(max_vars=5))
    set_quota("beta", QuotaPolicy(max_vars=10))
    rc = cmd_quota_list(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out

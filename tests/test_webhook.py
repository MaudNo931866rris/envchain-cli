"""Tests for envchain.webhook."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from envchain.webhook import (
    WebhookError,
    fire_webhook,
    get_webhook,
    list_webhooks,
    remove_webhook,
    set_webhook,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVCHAIN_DIR", str(tmp_path))
    yield tmp_path


def test_set_webhook_creates_entry():
    set_webhook("myproject", "https://example.com/hook")
    cfg = get_webhook("myproject")
    assert cfg is not None
    assert cfg["url"] == "https://example.com/hook"
    assert cfg["events"] == []


def test_set_webhook_with_events():
    set_webhook("proj", "https://example.com/hook", events=["set", "delete"])
    cfg = get_webhook("proj")
    assert cfg["events"] == ["set", "delete"]


def test_set_webhook_invalid_url_raises():
    with pytest.raises(WebhookError, match="Invalid webhook URL"):
        set_webhook("proj", "ftp://bad.url")


def test_set_webhook_empty_profile_raises():
    with pytest.raises(WebhookError, match="must not be empty"):
        set_webhook("", "https://example.com/hook")


def test_get_webhook_returns_none_when_not_set():
    assert get_webhook("nonexistent") is None


def test_remove_webhook_deletes_entry():
    set_webhook("proj", "https://example.com/hook")
    remove_webhook("proj")
    assert get_webhook("proj") is None


def test_remove_webhook_missing_raises():
    with pytest.raises(WebhookError, match="No webhook registered"):
        remove_webhook("ghost")


def test_list_webhooks_returns_all():
    set_webhook("a", "https://a.example.com/")
    set_webhook("b", "https://b.example.com/")
    result = list_webhooks()
    assert "a" in result
    assert "b" in result


def test_fire_webhook_returns_false_when_not_registered():
    assert fire_webhook("nobody", "set") is False


def test_fire_webhook_skips_filtered_event():
    set_webhook("proj", "https://example.com/hook", events=["delete"])
    # "set" is not in the allowed list — should be silently skipped
    result = fire_webhook("proj", "set")
    assert result is False


def test_fire_webhook_sends_post_on_match():
    set_webhook("proj", "https://example.com/hook", events=["set"])
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        result = fire_webhook("proj", "set", detail={"key": "FOO"})
    assert result is True
    mock_open.assert_called_once()
    req = mock_open.call_args[0][0]
    body = json.loads(req.data)
    assert body["profile"] == "proj"
    assert body["event"] == "set"
    assert body["detail"] == {"key": "FOO"}


def test_fire_webhook_all_events_when_list_empty():
    set_webhook("proj", "https://example.com/hook")
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = fire_webhook("proj", "any_event")
    assert result is True

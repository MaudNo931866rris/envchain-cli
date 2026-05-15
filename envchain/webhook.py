"""Webhook notifications for profile events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from envchain.store import _store_dir


class WebhookError(Exception):
    pass


def _webhooks_path() -> Path:
    return _store_dir() / "webhooks.json"


def _load_webhooks() -> dict:
    p = _webhooks_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_webhooks(data: dict) -> None:
    _webhooks_path().write_text(json.dumps(data, indent=2))


def set_webhook(profile: str, url: str, events: Optional[list[str]] = None) -> None:
    """Register a webhook URL for a profile, optionally filtered by event types."""
    if not profile:
        raise WebhookError("Profile name must not be empty.")
    if not url.startswith(("http://", "https://")):
        raise WebhookError(f"Invalid webhook URL: {url!r}")
    data = _load_webhooks()
    data[profile] = {"url": url, "events": events or []}
    _save_webhooks(data)


def remove_webhook(profile: str) -> None:
    """Remove the webhook registration for a profile."""
    data = _load_webhooks()
    if profile not in data:
        raise WebhookError(f"No webhook registered for profile {profile!r}.")
    del data[profile]
    _save_webhooks(data)


def get_webhook(profile: str) -> Optional[dict]:
    """Return webhook config for a profile, or None if not set."""
    return _load_webhooks().get(profile)


def list_webhooks() -> dict:
    """Return all registered webhooks keyed by profile name."""
    return _load_webhooks()


def fire_webhook(profile: str, event: str, detail: Optional[dict] = None) -> bool:
    """Send a POST request to the webhook URL if registered for this event.

    Returns True if the request was sent successfully, False otherwise.
    """
    cfg = get_webhook(profile)
    if cfg is None:
        return False
    allowed = cfg.get("events", [])
    if allowed and event not in allowed:
        return False
    payload = json.dumps({"profile": profile, "event": event, "detail": detail or {}}).encode()
    req = urllib.request.Request(
        cfg["url"],
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            return True
    except (urllib.error.URLError, OSError) as exc:
        raise WebhookError(f"Webhook delivery failed: {exc}") from exc

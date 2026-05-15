"""CLI commands for managing webhooks."""
from __future__ import annotations

import argparse
import sys

from envchain.webhook import (
    WebhookError,
    set_webhook,
    remove_webhook,
    get_webhook,
    list_webhooks,
)


def cmd_webhook_set(args: argparse.Namespace) -> int:
    events = [e.strip() for e in args.events.split(",")] if args.events else []
    try:
        set_webhook(args.profile, args.url, events or None)
    except WebhookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Webhook set for profile '{args.profile}'.")
    return 0


def cmd_webhook_remove(args: argparse.Namespace) -> int:
    try:
        remove_webhook(args.profile)
    except WebhookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Webhook removed for profile '{args.profile}'.")
    return 0


def cmd_webhook_show(args: argparse.Namespace) -> int:
    cfg = get_webhook(args.profile)
    if cfg is None:
        print(f"No webhook registered for profile '{args.profile}'.")
        return 0
    events = ", ".join(cfg["events"]) if cfg["events"] else "(all events)"
    print(f"URL:    {cfg['url']}")
    print(f"Events: {events}")
    return 0


def cmd_webhook_list(args: argparse.Namespace) -> int:  # noqa: ARG001
    webhooks = list_webhooks()
    if not webhooks:
        print("No webhooks registered.")
        return 0
    for profile, cfg in sorted(webhooks.items()):
        events = ", ".join(cfg["events"]) if cfg["events"] else "all"
        print(f"{profile:20s}  {cfg['url']}  [{events}]")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p_set = subparsers.add_parser("webhook-set", help="Register a webhook for a profile")
    p_set.add_argument("profile")
    p_set.add_argument("url")
    p_set.add_argument("--events", default="", help="Comma-separated event names to filter")
    p_set.set_defaults(func=cmd_webhook_set)

    p_rm = subparsers.add_parser("webhook-remove", help="Remove a webhook")
    p_rm.add_argument("profile")
    p_rm.set_defaults(func=cmd_webhook_remove)

    p_show = subparsers.add_parser("webhook-show", help="Show webhook for a profile")
    p_show.add_argument("profile")
    p_show.set_defaults(func=cmd_webhook_show)

    p_list = subparsers.add_parser("webhook-list", help="List all registered webhooks")
    p_list.set_defaults(func=cmd_webhook_list)

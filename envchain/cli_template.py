"""CLI commands for template rendering."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envchain.template import TemplateError, render_from_profile


def _prompt_passphrase(profile: str) -> str:
    import getpass
    return getpass.getpass(f"Passphrase for profile '{profile}': ")


def cmd_template_render(args: argparse.Namespace) -> int:
    """Render a template file (or stdin) using variables from a profile."""
    passphrase: str = getattr(args, "passphrase", None) or _prompt_passphrase(args.profile)

    if args.template_file == "-":
        template = sys.stdin.read()
    else:
        path = Path(args.template_file)
        if not path.exists():
            print(f"error: template file not found: {path}", file=sys.stderr)
            return 1
        template = path.read_text()

    try:
        rendered = render_from_profile(
            template,
            args.profile,
            passphrase,
            strict=not args.loose,
        )
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output and args.output != "-":
        Path(args.output).write_text(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "template",
        help="Render a template file using profile variables",
    )
    p.add_argument("profile", help="Profile name")
    p.add_argument(
        "template_file",
        metavar="TEMPLATE",
        help="Path to template file, or '-' to read from stdin",
    )
    p.add_argument("-o", "--output", default="-", help="Output file (default: stdout)")
    p.add_argument(
        "--loose",
        action="store_true",
        help="Leave unknown placeholders unchanged instead of raising an error",
    )
    p.add_argument("--passphrase", help="Passphrase (avoid; prefer interactive prompt)")
    p.set_defaults(func=cmd_template_render)

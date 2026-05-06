"""Command-line interface for envchain-cli."""

import os
import sys
import getpass
import argparse

from envchain import profile as prof


def cmd_set(args: argparse.Namespace) -> int:
    """Set one or more variables in a profile."""
    passphrase = getpass.getpass(f"Passphrase for profile '{args.profile}': ")
    p = prof.load(args.profile, passphrase)
    for item in args.var:
        if "=" not in item:
            print(f"Error: variable must be in KEY=VALUE format, got: {item}", file=sys.stderr)
            return 1
        key, value = item.split("=", 1)
        prof.set_var(p, key.strip(), value)
    prof.save(p, passphrase)
    print(f"Saved {len(args.var)} variable(s) to profile '{args.profile}'.")
    return 0


def cmd_unset(args: argparse.Namespace) -> int:
    """Remove variables from a profile."""
    passphrase = getpass.getpass(f"Passphrase for profile '{args.profile}': ")
    p = prof.load(args.profile, passphrase)
    for key in args.key:
        try:
            prof.unset_var(p, key)
        except KeyError:
            print(f"Warning: key '{key}' not found in profile '{args.profile}'.", file=sys.stderr)
    prof.save(p, passphrase)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List variable keys in a profile (values are hidden)."""
    passphrase = getpass.getpass(f"Passphrase for profile '{args.profile}': ")
    p = prof.load(args.profile, passphrase)
    keys = list(prof.as_env_dict(p).keys())
    if not keys:
        print(f"Profile '{args.profile}' is empty.")
    else:
        print(f"Variables in profile '{args.profile}':")
        for k in sorted(keys):
            print(f"  {k}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run a command with the profile's variables injected."""
    passphrase = getpass.getpass(f"Passphrase for profile '{args.profile}': ")
    p = prof.load(args.profile, passphrase)
    env = {**os.environ, **prof.as_env_dict(p)}
    os.execvpe(args.command[0], args.command, env)  # replaces current process
    return 0  # unreachable


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete an entire profile."""
    confirm = input(f"Delete profile '{args.profile}'? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return 0
    passphrase = getpass.getpass(f"Passphrase for profile '{args.profile}': ")
    p = prof.load(args.profile, passphrase)
    prof.delete(p)
    print(f"Profile '{args.profile}' deleted.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain",
        description="Manage and inject environment variable sets per project context.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd_name in ("set", "unset", "list", "run", "delete"):
        p = sub.add_parser(cmd_name)
        p.add_argument("profile", help="Profile name")
        if cmd_name == "set":
            p.add_argument("var", nargs="+", metavar="KEY=VALUE")
        elif cmd_name == "unset":
            p.add_argument("key", nargs="+")
        elif cmd_name == "run":
            p.add_argument("command", nargs=argparse.REMAINDER)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {
        "set": cmd_set,
        "unset": cmd_unset,
        "list": cmd_list,
        "run": cmd_run,
        "delete": cmd_delete,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()

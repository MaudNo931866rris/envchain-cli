"""CLI commands for profile ratings."""
from __future__ import annotations

import argparse
import sys

from envchain.rating import (
    RatingError,
    clear_rating,
    get_rating,
    list_ratings,
    set_rating,
    MIN_RATING,
    MAX_RATING,
)


def cmd_rating_set(args: argparse.Namespace) -> int:
    try:
        rating = set_rating(args.profile, args.rating)
        print(f"Rated profile '{args.profile}': {rating}/5")
        return 0
    except RatingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_rating_clear(args: argparse.Namespace) -> int:
    removed = clear_rating(args.profile)
    if removed:
        print(f"Rating cleared for profile '{args.profile}'.")
    else:
        print(f"No rating found for profile '{args.profile}'.")
    return 0


def cmd_rating_show(args: argparse.Namespace) -> int:
    rating = get_rating(args.profile)
    if rating is None:
        print(f"No rating set for profile '{args.profile}'.")
    else:
        stars = "★" * rating + "☆" * (MAX_RATING - rating)
        print(f"{args.profile}: {stars} ({rating}/{MAX_RATING})")
    return 0


def cmd_rating_list(args: argparse.Namespace) -> int:
    ratings = list_ratings()
    if not ratings:
        print("No ratings recorded.")
        return 0
    for profile, rating in ratings.items():
        stars = "★" * rating + "☆" * (MAX_RATING - rating)
        print(f"{profile}: {stars} ({rating}/{MAX_RATING})")
    return 0


def register(subparsers) -> None:
    p_set = subparsers.add_parser("rating-set", help="Set a star rating for a profile")
    p_set.add_argument("profile")
    p_set.add_argument("rating", type=int, help=f"Rating {MIN_RATING}–{MAX_RATING}")
    p_set.set_defaults(func=cmd_rating_set)

    p_clear = subparsers.add_parser("rating-clear", help="Remove rating for a profile")
    p_clear.add_argument("profile")
    p_clear.set_defaults(func=cmd_rating_clear)

    p_show = subparsers.add_parser("rating-show", help="Show rating for a profile")
    p_show.add_argument("profile")
    p_show.set_defaults(func=cmd_rating_show)

    p_list = subparsers.add_parser("rating-list", help="List all profile ratings")
    p_list.set_defaults(func=cmd_rating_list)

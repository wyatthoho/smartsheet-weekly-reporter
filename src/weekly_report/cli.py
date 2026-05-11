import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly report to clipboard.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--last-week",
        action="store_true",
        help="Generate report for last week instead of this week.",
    )
    group.add_argument(
        "--next-week",
        action="store_true",
        help="Generate report for next week instead of this week.",
    )
    return parser.parse_args()

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly report to clipboard.")
    parser.add_argument(
        "--last-week",
        action="store_true",
        help="Generate report for last week instead of this week.",
    )
    return parser.parse_args()

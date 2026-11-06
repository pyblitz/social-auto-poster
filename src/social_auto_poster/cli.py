"""Command-line interface.

Usage:
    social-auto-poster validate QUEUE.csv
    social-auto-poster list QUEUE.csv
    social-auto-poster run QUEUE.csv --publisher dry-run
    social-auto-poster run QUEUE.csv --publisher file-log --log-file posts.log

``run`` publishes every due (pending, time-arrived) post through the chosen
publisher, marks those posts ``published`` and saves the queue back.
"""

from __future__ import annotations

import argparse
import sys

from .publishers import ApiPublisher, DryRunPublisher, FileLogPublisher, Publisher
from .queue import load_queue, parse_datetime, save_queue
from .scheduler import due_posts, normalize_now, upcoming_posts


def _report_problems(errors: list[str]) -> bool:
    """Print load errors/warnings; return True if any were hard errors."""
    hard = False
    for err in errors:
        print(err, file=sys.stderr)
        if not err.startswith("warning:"):
            hard = True
    return hard


def cmd_validate(args: argparse.Namespace) -> int:
    posts, errors = load_queue(args.queue)
    if _report_problems(errors):
        return 1
    print(f"Queue OK: {len(posts)} valid post(s).")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    posts, errors = load_queue(args.queue)
    if _report_problems(errors):
        return 1
    now = normalize_now(None)
    for post in posts:
        marker = "DUE" if post.is_due(now) else post.status
        print(
            f"[{marker:>9}] {post.scheduled_at.isoformat()}  "
            f"{post.platform:<10} {post.caption[:60]}"
        )
    return 0


def _make_publisher(args: argparse.Namespace) -> Publisher:
    if args.publisher == "dry-run":
        return DryRunPublisher()
    if args.publisher == "file-log":
        if not args.log_file:
            raise SystemExit("--publisher file-log needs --log-file PATH")
        return FileLogPublisher(args.log_file)
    if args.publisher == "api":
        return ApiPublisher()
    raise SystemExit(f"unknown publisher: {args.publisher}")


def cmd_run(args: argparse.Namespace) -> int:
    posts, errors = load_queue(args.queue)
    if _report_problems(errors):
        return 1
    now = parse_datetime(args.now) if args.now else None
    due = due_posts(posts, now)
    if not due:
        print("Nothing due right now.")
        return 0

    publisher = _make_publisher(args)
    published = 0
    for post in due:
        try:
            result = publisher.publish(post)
        except RuntimeError as exc:
            print(f"FAILED ({post.platform}): {exc}", file=sys.stderr)
            continue
        if args.publisher != "dry-run":
            post.status = "published"
        published += 1
        if args.publisher == "dry-run":
            pass  # DryRunPublisher already printed the preview line.
        else:
            print(result)

    if args.publisher != "dry-run" and published:
        save_queue(args.queue, posts)
    waiting = len(upcoming_posts(posts, now))
    print(f"Done: {published} post(s) processed, {waiting} still scheduled ahead.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="social-auto-poster",
        description="Validate and publish a queue of scheduled social-media posts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="check a queue file for errors")
    p_validate.add_argument("queue", help="path to a .csv or .json queue file")
    p_validate.set_defaults(func=cmd_validate)

    p_list = sub.add_parser("list", help="show every post in the queue")
    p_list.add_argument("queue", help="path to a .csv or .json queue file")
    p_list.set_defaults(func=cmd_list)

    p_run = sub.add_parser("run", help="publish all due posts")
    p_run.add_argument("queue", help="path to a .csv or .json queue file")
    p_run.add_argument(
        "--publisher",
        choices=["dry-run", "file-log", "api"],
        default="dry-run",
        help="how to publish (default: dry-run preview)",
    )
    p_run.add_argument("--log-file", help="log file path for the file-log publisher")
    p_run.add_argument(
        "--now",
        help="pretend it is this ISO date/time (useful for testing a schedule)",
    )
    p_run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

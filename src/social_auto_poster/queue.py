"""Load, validate and save the post queue (CSV or JSON).

Queue format — one post per row/object with these fields:

    caption       (required) post text, up to 2200 characters
    image_path    (optional) path to an image file to attach
    scheduled_at  (required) ISO 8601 date/time, e.g. 2026-11-07T17:00:00
    platform      (required) one of: facebook, instagram, linkedin,
                             x, tiktok, youtube
    status        (optional) "pending" (default) or "published"

Times: if a value carries a UTC offset (or "Z") it is converted to naive
UTC; plain values are taken as local wall-clock time. Keep one convention
per queue file so comparisons stay meaningful.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import ALLOWED_PLATFORMS, MAX_CAPTION_LENGTH, STATUSES, Post


def parse_datetime(value: str) -> datetime:
    """Parse an ISO 8601 string into a naive datetime (UTC if offset given)."""
    dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def validate_fields(fields: dict, row: int) -> list[str]:
    """Return validation error messages for one raw queue entry."""
    errors: list[str] = []
    where = f"row {row}"

    caption = (fields.get("caption") or "").strip()
    if not caption:
        errors.append(f"{where}: caption is empty")
    elif len(caption) > MAX_CAPTION_LENGTH:
        errors.append(
            f"{where}: caption is {len(caption)} characters "
            f"(max {MAX_CAPTION_LENGTH})"
        )

    raw_when = (fields.get("scheduled_at") or "").strip()
    if not raw_when:
        errors.append(f"{where}: scheduled_at is missing")
    else:
        try:
            parse_datetime(raw_when)
        except ValueError:
            errors.append(
                f"{where}: scheduled_at {raw_when!r} is not a valid ISO 8601 date/time"
            )

    platform = (fields.get("platform") or "").strip().lower()
    if platform not in ALLOWED_PLATFORMS:
        errors.append(
            f"{where}: platform {platform!r} is not one of "
            f"{', '.join(ALLOWED_PLATFORMS)}"
        )

    status = (fields.get("status") or "pending").strip().lower()
    if status not in STATUSES:
        errors.append(f"{where}: status {status!r} must be one of {', '.join(STATUSES)}")

    return errors


def _to_post(fields: dict, row: int) -> Post:
    return Post(
        caption=(fields.get("caption") or "").strip(),
        scheduled_at=parse_datetime(fields.get("scheduled_at") or ""),
        platform=(fields.get("platform") or "").strip().lower(),
        image_path=(fields.get("image_path") or "").strip(),
        status=(fields.get("status") or "pending").strip().lower(),
        row=row,
    )


def load_queue(path: str | Path) -> tuple[list[Post], list[str]]:
    """Load a CSV or JSON queue file.

    Returns ``(posts, errors)``. Entries that fail validation are reported
    in ``errors`` and left out of ``posts``. Image files referenced by
    ``image_path`` produce a *warning* entry prefixed with ``"warning:"``
    if they do not exist, but the post still loads.
    """
    path = Path(path)
    if path.suffix.lower() == ".json":
        raw_rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_rows, list):
            return [], ["queue file: top-level JSON value must be a list of posts"]
    elif path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as fh:
            raw_rows = list(csv.DictReader(fh))
    else:
        return [], [f"queue file: unsupported extension {path.suffix!r} (use .csv or .json)"]

    posts: list[Post] = []
    errors: list[str] = []
    for i, fields in enumerate(raw_rows, start=1):
        if not isinstance(fields, dict):
            errors.append(f"row {i}: entry is not an object/row")
            continue
        row_errors = validate_fields(fields, i)
        if row_errors:
            errors.extend(row_errors)
            continue
        post = _to_post(fields, i)
        if post.image_path and not Path(post.image_path).exists():
            errors.append(
                f"warning: row {i}: image file not found: {post.image_path}"
            )
        posts.append(post)
    return posts, errors


def save_queue(path: str | Path, posts: list[Post]) -> None:
    """Write the queue back to disk (used to record published status)."""
    path = Path(path)
    records = [
        {
            "caption": p.caption,
            "image_path": p.image_path,
            "scheduled_at": p.scheduled_at.isoformat(),
            "platform": p.platform,
            "status": p.status,
        }
        for p in posts
    ]
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    else:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["caption", "image_path", "scheduled_at", "platform", "status"]
            )
            writer.writeheader()
            writer.writerows(records)

"""Scheduling logic: which posts are due right now."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import Post


def normalize_now(now: datetime | None) -> datetime:
    """Return a naive datetime for comparisons with parsed queue times."""
    if now is None:
        return datetime.now()
    if now.tzinfo is not None:
        return now.astimezone(timezone.utc).replace(tzinfo=None)
    return now


def due_posts(posts: list[Post], now: datetime | None = None) -> list[Post]:
    """Pending posts whose scheduled time has arrived, earliest first."""
    moment = normalize_now(now)
    return sorted((p for p in posts if p.is_due(moment)), key=lambda p: p.scheduled_at)


def upcoming_posts(posts: list[Post], now: datetime | None = None) -> list[Post]:
    """Pending posts scheduled for the future, earliest first."""
    moment = normalize_now(now)
    return sorted(
        (p for p in posts if p.status == "pending" and p.scheduled_at > moment),
        key=lambda p: p.scheduled_at,
    )

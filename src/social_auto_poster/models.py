"""Core data model for one scheduled post."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

#: Platforms this tool recognises as a post's target label.
ALLOWED_PLATFORMS = ("facebook", "instagram", "linkedin", "x", "tiktok", "youtube")

#: Lifecycle states a queued post can be in.
STATUSES = ("pending", "published")

MAX_CAPTION_LENGTH = 2200


@dataclass
class Post:
    """One entry from the queue file."""

    caption: str
    scheduled_at: datetime
    platform: str
    image_path: str = ""
    status: str = "pending"
    row: int = 0  # 1-based source row, used in validation messages

    def is_due(self, now: datetime) -> bool:
        """True when the post is still pending and its time has arrived."""
        return self.status == "pending" and self.scheduled_at <= now

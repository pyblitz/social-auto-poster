"""Pluggable publishers.

A publisher takes one :class:`~social_auto_poster.models.Post` and returns a
short human-readable result string.

Included publishers:

* ``DryRunPublisher`` — prints what *would* be posted; touches nothing.
  Use it to preview a run safely.
* ``FileLogPublisher`` — appends one JSON record per post to a log file.
  Useful as an audit trail for client work.
* ``ApiPublisher`` — the integration point for real platforms. Real posting
  needs the account owner's own API credentials (read from environment
  variables); until an integration is wired up for a platform it raises
  ``RuntimeError`` instead of pretending a post went out.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from .models import Post


class Publisher(ABC):
    """Base class for anything that can 'publish' a post."""

    name = "base"

    @abstractmethod
    def publish(self, post: Post) -> str:
        """Publish one post and return a short result description."""
        raise NotImplementedError


class DryRunPublisher(Publisher):
    """Preview publisher: reports what would be posted, changes nothing."""

    name = "dry-run"

    def __init__(self, out=print):
        self._out = out

    def publish(self, post: Post) -> str:
        message = (
            f"[dry-run] would post to {post.platform} "
            f"(scheduled {post.scheduled_at.isoformat()}): "
            f"{post.caption}"
        )
        if post.image_path:
            message += f" [image: {post.image_path}]"
        self._out(message)
        return message


class FileLogPublisher(Publisher):
    """Appends one JSON line per published post to a log file."""

    name = "file-log"

    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)

    def publish(self, post: Post) -> str:
        record = {
            "published_at": datetime.now().isoformat(timespec="seconds"),
            "platform": post.platform,
            "caption": post.caption,
            "image_path": post.image_path,
            "scheduled_at": post.scheduled_at.isoformat(),
        }
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return f"logged to {self.log_path}: {post.platform} post at {record['published_at']}"


class ApiPublisher(Publisher):
    """Placeholder for real platform APIs.

    Real posting requires the *account owner's own* API credentials, read
    from environment variables named ``SOCIAL_POSTER_<PLATFORM>_TOKEN``
    (for example ``SOCIAL_POSTER_FACEBOOK_TOKEN``). This class never fakes
    a successful post: with no token configured — or no integration built
    yet for the platform — it raises ``RuntimeError`` with instructions.
    """

    name = "api"

    def __init__(self, environ: dict | None = None):
        self._environ = os.environ if environ is None else environ

    def token_for(self, platform: str) -> str | None:
        return self._environ.get(f"SOCIAL_POSTER_{platform.upper()}_TOKEN")

    def publish(self, post: Post) -> str:
        token = self.token_for(post.platform)
        if not token:
            raise RuntimeError(
                f"No API credentials for {post.platform}: set the environment "
                f"variable SOCIAL_POSTER_{post.platform.upper()}_TOKEN with the "
                "account owner's own token to enable real posting."
            )
        raise RuntimeError(
            f"Real posting to {post.platform} is not wired up in this build yet. "
            "A token is present; add the platform integration in publishers.py "
            "before relying on it — this tool never reports a post it did not make."
        )

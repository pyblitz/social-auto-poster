"""Scheduling logic tests."""

from datetime import datetime

from social_auto_poster.models import Post
from social_auto_poster.scheduler import due_posts, upcoming_posts

NOW = datetime(2026, 11, 6, 12, 0, 0)


def _post(caption, when, status="pending"):
    return Post(caption=caption, scheduled_at=when, platform="instagram", status=status)


def test_past_pending_post_is_due():
    posts = [_post("old", datetime(2026, 11, 6, 9, 0))]
    assert [p.caption for p in due_posts(posts, NOW)] == ["old"]


def test_future_post_is_not_due():
    posts = [_post("later", datetime(2026, 11, 7, 9, 0))]
    assert due_posts(posts, NOW) == []
    assert [p.caption for p in upcoming_posts(posts, NOW)] == ["later"]


def test_already_published_post_is_never_due():
    posts = [_post("done", datetime(2026, 11, 1, 9, 0), status="published")]
    assert due_posts(posts, NOW) == []
    assert upcoming_posts(posts, NOW) == []


def test_due_posts_come_out_earliest_first():
    posts = [
        _post("second", datetime(2026, 11, 6, 10, 0)),
        _post("first", datetime(2026, 11, 6, 8, 0)),
    ]
    assert [p.caption for p in due_posts(posts, NOW)] == ["first", "second"]

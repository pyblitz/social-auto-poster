"""Publisher behaviour tests."""

import json
from datetime import datetime

import pytest

from social_auto_poster.models import Post
from social_auto_poster.publishers import ApiPublisher, DryRunPublisher, FileLogPublisher


def _post():
    return Post(
        caption="Hello from the test suite",
        scheduled_at=datetime(2026, 11, 6, 9, 0),
        platform="instagram",
    )


def test_dry_run_reports_without_side_effects():
    printed = []
    result = DryRunPublisher(out=printed.append).publish(_post())
    assert "dry-run" in result
    assert "instagram" in result
    assert printed == [result]


def test_file_log_appends_a_json_record(tmp_path):
    log = tmp_path / "published.log"
    publisher = FileLogPublisher(log)
    publisher.publish(_post())
    publisher.publish(_post())
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    record = json.loads(lines[0])
    assert record["platform"] == "instagram"
    assert record["caption"] == "Hello from the test suite"


def test_api_publisher_without_token_raises():
    publisher = ApiPublisher(environ={})
    with pytest.raises(RuntimeError, match="SOCIAL_POSTER_INSTAGRAM_TOKEN"):
        publisher.publish(_post())


def test_api_publisher_never_fakes_a_post():
    # Even with a token present, an unwired platform must refuse loudly
    # rather than claim success.
    publisher = ApiPublisher(environ={"SOCIAL_POSTER_INSTAGRAM_TOKEN": "test-token"})
    with pytest.raises(RuntimeError, match="not wired up"):
        publisher.publish(_post())

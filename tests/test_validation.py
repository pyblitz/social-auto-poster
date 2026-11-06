"""Validation tests for queue loading."""

from social_auto_poster.queue import load_queue, validate_fields


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_csv_loads(tmp_path):
    queue = _write(
        tmp_path,
        "q.csv",
        "caption,image_path,scheduled_at,platform,status\n"
        "Hello world,,2026-11-07T17:00:00,instagram,pending\n",
    )
    posts, errors = load_queue(queue)
    assert errors == []
    assert len(posts) == 1
    assert posts[0].platform == "instagram"
    assert posts[0].status == "pending"


def test_valid_json_loads(tmp_path):
    queue = _write(
        tmp_path,
        "q.json",
        '[{"caption": "Hi", "scheduled_at": "2026-11-07T17:00:00",'
        ' "platform": "facebook"}]',
    )
    posts, errors = load_queue(queue)
    assert errors == []
    assert len(posts) == 1
    assert posts[0].image_path == ""  # optional field defaults to empty


def test_empty_caption_is_an_error(tmp_path):
    queue = _write(
        tmp_path,
        "q.csv",
        "caption,image_path,scheduled_at,platform\n"
        ",,2026-11-07T17:00:00,instagram\n",
    )
    posts, errors = load_queue(queue)
    assert posts == []
    assert any("caption is empty" in e for e in errors)


def test_bad_datetime_is_an_error():
    errors = validate_fields(
        {"caption": "Hi", "scheduled_at": "next friday", "platform": "facebook"}, row=3
    )
    assert any("row 3" in e and "scheduled_at" in e for e in errors)


def test_unknown_platform_is_an_error():
    errors = validate_fields(
        {"caption": "Hi", "scheduled_at": "2026-11-07T17:00:00", "platform": "myspace"},
        row=1,
    )
    assert any("platform" in e for e in errors)


def test_overlong_caption_is_an_error():
    errors = validate_fields(
        {
            "caption": "x" * 2201,
            "scheduled_at": "2026-11-07T17:00:00",
            "platform": "facebook",
        },
        row=1,
    )
    assert any("caption" in e for e in errors)


def test_missing_image_is_a_warning_not_an_error(tmp_path):
    queue = _write(
        tmp_path,
        "q.csv",
        "caption,image_path,scheduled_at,platform\n"
        "Hi,images/nope.png,2026-11-07T17:00:00,instagram\n",
    )
    posts, errors = load_queue(queue)
    assert len(posts) == 1  # post still loads
    assert any(e.startswith("warning:") for e in errors)

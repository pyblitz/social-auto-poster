# Social Auto Poster

A small command-line tool that publishes scheduled social-media posts from
a simple queue file. A freelancer prepares the queue once — in a spreadsheet
saved as CSV, or as JSON — and the tool validates every entry, then
"publishes" the posts whose time has arrived through a pluggable publisher.

Pure Python standard library: no dependencies to install.

## What it does

* Reads a post queue from **CSV or JSON**: caption, image path, date/time,
  platform label, status.
* **Validates** the whole queue before anything runs: empty or overlong
  captions, unparseable dates, unknown platforms and bad statuses are
  reported with row numbers. A missing image file is a warning, not an
  error.
* **Scheduling logic**: a post is *due* when it is still `pending` and its
  scheduled time has arrived; due posts are processed earliest first.
* **Pluggable publishers**:
  * `dry-run` — prints exactly what would be posted, changes nothing.
    The safe way to preview a run.
  * `file-log` — appends one JSON record per post to a log file, giving a
    verifiable record of what went out and when.
  * `api` — the integration point for real platforms (see below).
* After a real run, published posts are marked `published` in the queue
  file itself, so nothing is ever sent twice by accident.

## Honest note about "real" posting

Posting to an actual platform account requires the **account owner's own
API credentials** — there is no legitimate shortcut around that. This tool
reads them from environment variables named `SOCIAL_POSTER_<PLATFORM>_TOKEN`
(e.g. `SOCIAL_POSTER_FACEBOOK_TOKEN`). Until a platform integration is
wired up with such a token, the `api` publisher refuses with a clear error
instead of pretending a post went out. The dry-run and file-log publishers
are fully working today and are what a schedule is rehearsed and recorded
with.

## Install

```bash
pip install -e .
```

## The queue file

CSV (save any spreadsheet in this shape) — see `examples/queue.csv`:

```csv
caption,image_path,scheduled_at,platform,status
"Fresh designs dropping this week",,2026-11-07T17:00:00,instagram,pending
"New logo reveal",images/logo.png,2026-11-08T10:00:00,facebook,pending
```

Fields: `caption` (required, up to 2200 characters), `image_path`
(optional), `scheduled_at` (required, ISO 8601), `platform` (one of
facebook, instagram, linkedin, x, tiktok, youtube), `status` (optional,
`pending` by default). JSON queues use the same field names — see
`examples/queue.json`. Times with a UTC offset are converted to UTC; plain
times are treated as local wall-clock, so keep one convention per file.

## Use

```bash
# 1. Check a queue for mistakes before anything runs
social-auto-poster validate examples/queue.csv

# 2. See what is in the queue and what is due
social-auto-poster list examples/queue.csv

# 3. Preview a run — nothing is changed
social-auto-poster run examples/queue.csv --publisher dry-run

# 4. Run for real (records each post to a log, marks the queue)
social-auto-poster run examples/queue.csv \
  --publisher file-log --log-file published.log

# Test a future moment without waiting for it
social-auto-poster run examples/queue.csv --publisher dry-run \
  --now 2099-01-02T00:00:00
```

The same commands work with `python -m social_auto_poster` in place of
`social-auto-poster`.

## How a business client uses this (the service workflow)

1. The client (or the freelancer, from the client's content) fills in the
   queue spreadsheet: captions, image paths, dates, platforms.
2. The freelancer runs `validate` — typos and missing images are caught
   before they can cost a posting slot.
3. Each day (or on an agreed schedule) the freelancer runs the tool:
   first `dry-run` to confirm exactly what is about to go out, then the
   real run.
4. The client receives the queue file (everything sent is marked
   `published`) plus the log file — a plain, checkable record of every
   post, its platform and its time.

## Test

```bash
python -m pytest
```

## Why this exists

Built by Shoaib Ahmed (Python developer + graphic designer) as a portfolio
project and as the working tool behind his social-media automation service
for small businesses: the same weekly content queue he manages for clients,
packaged so the process is repeatable, validated and auditable.

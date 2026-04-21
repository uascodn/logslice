"""Tests for logslice.histogram_cli."""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from logslice.histogram_cli import build_histogram_parser, run_histogram


def _args(**kwargs):
    defaults = {
        "file": "-",
        "bucket": "1m",
        "ts_field": "timestamp",
        "count_field": None,
        "output_json": False,
        "bar_width": 40,
    }
    defaults.update(kwargs)
    import argparse
    ns = argparse.Namespace(**defaults)
    return ns


def _jsonl(*minutes: int) -> list[str]:
    lines = []
    for m in minutes:
        ts = datetime(2024, 1, 1, 12, m, 0, tzinfo=timezone.utc).isoformat()
        lines.append(json.dumps({"timestamp": ts, "level": "info"}) + "\n")
    return lines


def test_build_histogram_parser_returns_parser():
    p = build_histogram_parser()
    assert p is not None
    args = p.parse_args(["--bucket", "5m"])
    assert args.bucket == "5m"


def test_run_histogram_ascii_output():
    lines = _jsonl(0, 0, 1)
    out = io.StringIO()
    with patch("sys.stdin", io.StringIO("".join(lines))):
        run_histogram(_args(), out=out)
    result = out.getvalue()
    assert "#" in result
    assert "2" in result  # two records in minute 0


def test_run_histogram_json_output():
    lines = _jsonl(0, 0, 1)
    out = io.StringIO()
    with patch("sys.stdin", io.StringIO("".join(lines))):
        run_histogram(_args(output_json=True), out=out)
    payload = json.loads(out.getvalue())
    assert isinstance(payload, list)
    assert any(entry["count"] == 2 for entry in payload)


def test_run_histogram_json_has_iso_bucket():
    lines = _jsonl(0)
    out = io.StringIO()
    with patch("sys.stdin", io.StringIO("".join(lines))):
        run_histogram(_args(output_json=True), out=out)
    payload = json.loads(out.getvalue())
    assert "bucket" in payload[0]
    # Should parse as ISO datetime without error
    datetime.fromisoformat(payload[0]["bucket"])


def test_run_histogram_bad_bucket_exits(capsys):
    out = io.StringIO()
    with patch("sys.stdin", io.StringIO("")), pytest.raises(SystemExit) as exc_info:
        run_histogram(_args(bucket="99x"), out=out)
    assert exc_info.value.code == 1


def test_run_histogram_empty_input_no_data():
    out = io.StringIO()
    with patch("sys.stdin", io.StringIO("")):
        run_histogram(_args(), out=out)
    assert "(no data)" in out.getvalue()


def test_run_histogram_custom_bar_width():
    lines = _jsonl(0, 0)
    out = io.StringIO()
    with patch("sys.stdin", io.StringIO("".join(lines))):
        run_histogram(_args(bar_width=20), out=out)
    result = out.getvalue()
    # Bar should not exceed 20 '#' chars
    for line in result.splitlines():
        if "|" in line:
            bar_part = line.split("|")[1]
            assert bar_part.count("#") <= 20

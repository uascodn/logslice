"""Tests for logslice.histogram."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from logslice.histogram import (
    build_histogram,
    bucket_timestamp,
    parse_bucket_expr,
    render_histogram,
)


# ---------------------------------------------------------------------------
# parse_bucket_expr
# ---------------------------------------------------------------------------

def test_parse_seconds():
    assert parse_bucket_expr("30s") == timedelta(seconds=30)


def test_parse_minutes():
    assert parse_bucket_expr("5m") == timedelta(minutes=5)


def test_parse_hours():
    assert parse_bucket_expr("2h") == timedelta(hours=2)


def test_parse_days():
    assert parse_bucket_expr("1d") == timedelta(days=1)


def test_parse_invalid_unit():
    with pytest.raises(ValueError, match="Unknown time unit"):
        parse_bucket_expr("10x")


def test_parse_invalid_number():
    with pytest.raises(ValueError, match="Invalid bucket size"):
        parse_bucket_expr("abcm")


def test_parse_zero_raises():
    with pytest.raises(ValueError, match="positive"):
        parse_bucket_expr("0m")


# ---------------------------------------------------------------------------
# bucket_timestamp
# ---------------------------------------------------------------------------

def test_bucket_timestamp_floors_to_minute():
    ts = datetime(2024, 1, 1, 12, 34, 56, tzinfo=timezone.utc)
    result = bucket_timestamp(ts, timedelta(minutes=1))
    assert result == datetime(2024, 1, 1, 12, 34, 0, tzinfo=timezone.utc)


def test_bucket_timestamp_five_minute_bucket():
    ts = datetime(2024, 1, 1, 12, 37, 0, tzinfo=timezone.utc)
    result = bucket_timestamp(ts, timedelta(minutes=5))
    assert result == datetime(2024, 1, 1, 12, 35, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# build_histogram
# ---------------------------------------------------------------------------

def _rec(minute: int, second: int = 0) -> dict:
    ts = datetime(2024, 1, 1, 12, minute, second, tzinfo=timezone.utc)
    return {"timestamp": ts.isoformat(), "level": "info"}


def test_build_histogram_counts():
    records = [_rec(0), _rec(0, 30), _rec(1), _rec(2)]
    hist = build_histogram(records, timedelta(minutes=1))
    counts = {b.minute: c for b, c in hist}
    assert counts[0] == 2
    assert counts[1] == 1
    assert counts[2] == 1


def test_build_histogram_sorted():
    records = [_rec(5), _rec(1), _rec(3)]
    hist = build_histogram(records, timedelta(minutes=1))
    buckets = [b for b, _ in hist]
    assert buckets == sorted(buckets)


def test_build_histogram_skips_missing_ts():
    records = [{"level": "info"}, _rec(0)]
    hist = build_histogram(records, timedelta(minutes=1))
    assert len(hist) == 1


def test_build_histogram_sum_field():
    records = [
        {"timestamp": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(), "latency": 10},
        {"timestamp": datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc).isoformat(), "latency": 20},
    ]
    hist = build_histogram(records, timedelta(minutes=1), count_field="latency")
    assert hist[0][1] == 30


# ---------------------------------------------------------------------------
# render_histogram
# ---------------------------------------------------------------------------

def test_render_histogram_no_data():
    assert render_histogram([]) == "(no data)"


def test_render_histogram_contains_count():
    ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    output = render_histogram([(ts, 5)], bar_width=10)
    assert "5" in output
    assert "#" in output


def test_render_histogram_max_bar_for_max_count():
    ts1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
    output = render_histogram([(ts1, 10), (ts2, 5)], bar_width=10)
    lines = output.splitlines()
    bar1 = lines[0].split("|")[1]
    assert bar1.count("#") == 10

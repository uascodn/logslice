"""Tests for logslice.rate."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from logslice.rate import compute_rate, parse_rate_expr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rec(ts: str, **extra) -> dict:
    return {"timestamp": ts, **extra}


def _ts(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# parse_rate_expr
# ---------------------------------------------------------------------------

def test_parse_rate_expr_seconds():
    result = parse_rate_expr("10s")
    assert result["bucket_seconds"] == 10
    assert result["group_by"] is None


def test_parse_rate_expr_minutes():
    result = parse_rate_expr("2m")
    assert result["bucket_seconds"] == 120


def test_parse_rate_expr_with_group():
    result = parse_rate_expr("1m:level")
    assert result["bucket_seconds"] == 60
    assert result["group_by"] == "level"


def test_parse_rate_expr_invalid_too_many_colons():
    with pytest.raises(ValueError):
        parse_rate_expr("1m:level:extra")


def test_parse_rate_expr_invalid_unit():
    with pytest.raises(ValueError):
        parse_rate_expr("5x")


# ---------------------------------------------------------------------------
# compute_rate
# ---------------------------------------------------------------------------

def test_compute_rate_single_bucket():
    records = [_rec(_ts(0)), _rec(_ts(5)), _rec(_ts(9))]
    results = list(compute_rate(records, bucket_seconds=60))
    assert len(results) == 1
    assert results[0]["count"] == 3
    assert results[0]["rate_per_sec"] == pytest.approx(3 / 60)


def test_compute_rate_two_buckets():
    records = [_rec(_ts(0)), _rec(_ts(60)), _rec(_ts(61))]
    results = list(compute_rate(records, bucket_seconds=60))
    assert len(results) == 2
    assert results[0]["count"] == 1
    assert results[1]["count"] == 2


def test_compute_rate_skips_records_without_timestamp():
    records = [{"msg": "no ts"}, _rec(_ts(0))]
    results = list(compute_rate(records, bucket_seconds=60))
    assert len(results) == 1
    assert results[0]["count"] == 1


def test_compute_rate_group_by():
    records = [
        _rec(_ts(0), level="error"),
        _rec(_ts(5), level="info"),
        _rec(_ts(10), level="error"),
    ]
    results = list(compute_rate(records, bucket_seconds=60, group_by="level"))
    assert len(results) == 2
    groups = {r["group"]: r["count"] for r in results}
    assert groups["error"] == 2
    assert groups["info"] == 1


def test_compute_rate_group_by_present_in_output():
    records = [_rec(_ts(0), level="warn")]
    results = list(compute_rate(records, bucket_seconds=10, group_by="level"))
    assert "group" in results[0]
    assert results[0]["group"] == "warn"


def test_compute_rate_no_group_key_absent():
    records = [_rec(_ts(0))]
    results = list(compute_rate(records, bucket_seconds=10))
    assert "group" not in results[0]


def test_compute_rate_empty_input():
    assert list(compute_rate([], bucket_seconds=60)) == []

"""Tests for logslice.resample and logslice.resample_cli."""

from __future__ import annotations

import json
from io import StringIO

import pytest

from logslice.resample import parse_resample_expr, resample_records


# ---------------------------------------------------------------------------
# parse_resample_expr
# ---------------------------------------------------------------------------

def test_parse_seconds():
    secs, agg = parse_resample_expr("30s:count")
    assert secs == 30
    assert agg == "count"


def test_parse_minutes():
    secs, agg = parse_resample_expr("5m:sum:bytes")
    assert secs == 300
    assert agg == "sum:bytes"


def test_parse_hours():
    secs, agg = parse_resample_expr("1h:avg:latency")
    assert secs == 3600
    assert agg == "avg:latency"


def test_parse_days():
    secs, agg = parse_resample_expr("2d:max:score")
    assert secs == 172800
    assert agg == "max:score"


def test_parse_invalid_unit():
    with pytest.raises(ValueError, match="invalid interval"):
        parse_resample_expr("5x:count")


def test_parse_missing_agg():
    with pytest.raises(ValueError, match="resample expression"):
        parse_resample_expr("5m")


# ---------------------------------------------------------------------------
# resample_records helpers
# ---------------------------------------------------------------------------

def _rec(ts: str, **kwargs) -> dict:
    return {"timestamp": ts, **kwargs}


BASE = "2024-01-01T00:"

RECORDS = [
    _rec(f"{BASE}00:10Z", latency=100, bytes=512),
    _rec(f"{BASE}00:50Z", latency=200, bytes=256),
    _rec(f"{BASE}01:30Z", latency=150, bytes=1024),
    _rec(f"{BASE}02:00Z", latency=50,  bytes=128),
]


def test_count_single_bucket():
    rows = resample_records(RECORDS, 300, "count")  # 5-min buckets
    assert len(rows) == 1
    assert rows[0]["value"] == 4
    assert rows[0]["agg"] == "count"


def test_count_two_buckets():
    rows = resample_records(RECORDS, 60, "count")  # 1-min buckets
    assert len(rows) == 3
    counts = [r["value"] for r in rows]
    assert counts == [2, 1, 1]


def test_sum_field():
    rows = resample_records(RECORDS, 300, "sum", "bytes")
    assert rows[0]["value"] == pytest.approx(512 + 256 + 1024 + 128)
    assert rows[0]["field"] == "bytes"


def test_avg_field():
    rows = resample_records(RECORDS, 300, "avg", "latency")
    expected = (100 + 200 + 150 + 50) / 4
    assert rows[0]["value"] == pytest.approx(expected)


def test_min_max_field():
    rows_min = resample_records(RECORDS, 300, "min", "latency")
    rows_max = resample_records(RECORDS, 300, "max", "latency")
    assert rows_min[0]["value"] == pytest.approx(50)
    assert rows_max[0]["value"] == pytest.approx(200)


def test_agg_requires_field():
    with pytest.raises(ValueError, match="requires a field"):
        resample_records(RECORDS, 60, "sum")


def test_unknown_agg():
    with pytest.raises(ValueError, match="unknown aggregation"):
        resample_records(RECORDS, 60, "median", "latency")


def test_records_without_timestamp_skipped():
    mixed = [{"msg": "no ts"}, *RECORDS]
    rows = resample_records(mixed, 300, "count")
    assert rows[0]["value"] == 4


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def test_run_resample_json_output(tmp_path):
    from logslice.resample_cli import build_resample_parser, run_resample

    log = tmp_path / "log.jsonl"
    log.write_text(
        "\n".join(json.dumps(_rec(f"{BASE}{m:02d}:00Z", bytes=100)) for m in range(4)) + "\n"
    )
    parser = build_resample_parser()
    args = parser.parse_args(["2m:count", str(log)])
    out = StringIO()
    run_resample(args, out=out)
    lines = [l for l in out.getvalue().splitlines() if l.strip()]
    rows = [json.loads(l) for l in lines]
    assert all(r["agg"] == "count" for r in rows)
    assert sum(r["value"] for r in rows) == 4


def test_run_resample_table_output(tmp_path):
    from logslice.resample_cli import build_resample_parser, run_resample

    log = tmp_path / "log.jsonl"
    log.write_text(
        "\n".join(json.dumps(_rec(f"{BASE}00:0{i}Z", latency=10 * i)) for i in range(3)) + "\n"
    )
    parser = build_resample_parser()
    args = parser.parse_args(["5m:avg:latency", str(log), "--format", "table"])
    out = StringIO()
    run_resample(args, out=out)
    text = out.getvalue()
    assert "bucket" in text
    assert "value" in text

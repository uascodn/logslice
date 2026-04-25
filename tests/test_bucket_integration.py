"""Integration tests for the bucket feature end-to-end."""
import json

from logslice.bucket import bucket_records, parse_bucket_field_expr, render_bucket_summary
from logslice.parser import parse_line


def _make_jsonl_records(raw_lines):
    return [parse_line(line) for line in raw_lines if line.strip()]


_LINES = [
    '{"level": "info",  "service": "api",   "msg": "ok"}',
    '{"level": "error", "service": "api",   "msg": "fail"}',
    '{"level": "info",  "service": "worker","msg": "done"}',
    '{"level": "warn",  "service": "api",   "msg": "slow"}',
    '{"level": "error", "service": "worker","msg": "crash"}',
    '{"service": "db",  "msg": "no level"}',
]


def test_integration_bucket_by_level():
    records = _make_jsonl_records(_LINES)
    field, buckets = parse_bucket_field_expr("level")
    groups = bucket_records(records, field, buckets)
    assert len(groups["info"]) == 2
    assert len(groups["error"]) == 2
    assert len(groups["warn"]) == 1
    assert len(groups["__missing__"]) == 1


def test_integration_bucket_by_service():
    records = _make_jsonl_records(_LINES)
    groups = bucket_records(records, "service")
    assert len(groups["api"]) == 3
    assert len(groups["worker"]) == 2
    assert len(groups["db"]) == 1


def test_integration_restricted_buckets_other():
    records = _make_jsonl_records(_LINES)
    field, buckets = parse_bucket_field_expr("level:info,error")
    groups = bucket_records(records, field, buckets)
    assert "warn" not in groups
    assert len(groups["__other__"]) == 1  # the warn record
    assert len(groups["__missing__"]) == 1


def test_integration_render_summary_percentages():
    records = _make_jsonl_records(_LINES)
    groups = bucket_records(records, "level")
    summary = render_bucket_summary(groups, "level")
    # 6 total records; info=2 => 33.3%
    assert "%" in summary
    assert "6" in summary  # total


def test_integration_empty_file():
    records = _make_jsonl_records([])
    groups = bucket_records(records, "level")
    assert groups == {}
    summary = render_bucket_summary(groups, "level")
    assert "TOTAL" in summary
    assert "0" in summary

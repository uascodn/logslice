"""Tests for logslice.pipeline — build_pipeline and run_pipeline."""

import pytest
from unittest.mock import patch, MagicMock
from logslice.pipeline import build_pipeline, run_pipeline


def make_json_line(fields: dict) -> str:
    import json
    return json.dumps(fields)


LINES = [
    make_json_line({"time": "2024-01-01T00:00:00Z", "level": "info",  "msg": "startup",  "service": "api"}),
    make_json_line({"time": "2024-01-01T:00Z", "level": "error", "msg": "crash",    "service": "api"}),
    make_json_line({"time": "2024-01-01T00:02:00Z", "level": "info",  "msg": "recovery", "service": "worker"}),
    make_json_line({"time": "2024-01-01T00:03:00Z", "level": "debug", "msg": "tick",     "service": "worker"}),
]


def _args(**kwargs):
    """Build a minimal namespace mimicking parsed CLI args."""
    defaults = dict(
        start=None,
        end=None,
        filters=[],
        transforms=[],
        sample=None,
        dedupe=False,
        dedupe_fields=None,
        keep_fields=None,
        drop_fields=None,
        output_format="json",
        highlight=False,
        highlight_pattern=None,
        no_pager=True,
    )
    defaults.update(kwargs)
    return MagicMock(**defaults)


def test_build_pipeline_returns_callable():
    args = _args()
    pipeline = build_pipeline(args)
    assert callable(pipeline)


def test_run_pipeline_no_filters():
    args = _args()
    results = list(run_pipeline(LINES, args))
    assert len(results) == len(LINES)


def test_run_pipeline_filter_by_level():
    args = _args(filters=["level=error"])
    results = list(run_pipeline(LINES, args))
    assert len(results) == 1
    assert "crash" in results[0]


def test_run_pipeline_time_start():
    args = _args(start="2024-01-01T00:02:00Z")
    results = list(run_pipeline(LINES, args))
    assert len(results) == 2


def test_run_pipeline_time_end():
    args = _args(end="2024-01-01T00:01:00Z")
    results = list(run_pipeline(LINES, args))
    assert len(results) == 2


def test_run_pipeline_time_range():
    args = _args(start="2024-01-01T00:01:00Z", end="2024-01-01T00:02:00Z")
    results = list(run_pipeline(LINES, args))
    assert len(results) == 2


def test_run_pipeline_drop_fields():
    args = _args(drop_fields=["service"])
    results = list(run_pipeline(LINES, args))
    assert all("service" not in r for r in results)


def test_run_pipeline_keep_fields():
    args = _args(keep_fields=["msg", "level"])
    results = list(run_pipeline(LINES, args))
    for r in results:
        assert "msg" in r
        assert "service" not in r


def test_run_pipeline_dedupe():
    duped = LINES + LINES
    args = _args(dedupe=True)
    results = list(run_pipeline(duped, args))
    assert len(results) == len(LINES)


def test_run_pipeline_empty_input():
    args = _args()
    results = list(run_pipeline([], args))
    assert results == []


def test_run_pipeline_skips_unparseable_lines():
    lines = ["not json or logfmt!!!", LINES[0]]
    args = _args()
    # Unparseable lines should be silently skipped; only the valid line is returned.
    results = list(run_pipeline(lines, args))
    assert len(results) == 1
    assert "startup" in results[0]


def test_run_pipeline_filter_by_service():
    """Filter on a non-level field to verify generic key=value filtering works."""
    args = _args(filters=["service=worker"])
    results = list(run_pipeline(LINES, args))
    assert len(results) == 2
    assert all("worker" in r for r in results)

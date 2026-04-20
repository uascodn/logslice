"""Tests for logslice.window_cli."""

import io
import json
import textwrap

import pytest

from logslice.window_cli import build_window_parser, run_window


def _args(**kwargs):
    defaults = {"file": "-", "size": "1m", "agg": "count", "ts_field": "timestamp"}
    defaults.update(kwargs)
    import argparse
    ns = argparse.Namespace(**defaults)
    return ns


def _jsonl(*records) -> str:
    return "\n".join(json.dumps(r) for r in records) + "\n"


def test_build_window_parser_returns_parser():
    p = build_window_parser()
    assert p is not None


def test_run_window_count_single_window(monkeypatch):
    lines = _jsonl(
        {"timestamp": "2024-01-01T00:00:10Z", "level": "info"},
        {"timestamp": "2024-01-01T00:00:30Z", "level": "error"},
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(lines))
    out = io.StringIO()
    run_window(_args(size="1m"), out=out)
    results = [json.loads(l) for l in out.getvalue().strip().splitlines()]
    assert len(results) == 1
    assert results[0]["count"] == 2
    assert results[0]["window_count"] == 2


def test_run_window_count_two_windows(monkeypatch):
    lines = _jsonl(
        {"timestamp": "2024-01-01T00:00:10Z"},
        {"timestamp": "2024-01-01T00:01:15Z"},
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(lines))
    out = io.StringIO()
    run_window(_args(size="1m"), out=out)
    results = [json.loads(l) for l in out.getvalue().strip().splitlines()]
    assert len(results) == 2


def test_run_window_level_count_agg(monkeypatch):
    lines = _jsonl(
        {"timestamp": "2024-01-01T00:00:01Z", "level": "info"},
        {"timestamp": "2024-01-01T00:00:02Z", "level": "error"},
        {"timestamp": "2024-01-01T00:00:03Z", "level": "info"},
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(lines))
    out = io.StringIO()
    run_window(_args(size="1m", agg="level_count"), out=out)
    results = [json.loads(l) for l in out.getvalue().strip().splitlines()]
    assert results[0]["levels"]["info"] == 2
    assert results[0]["levels"]["error"] == 1


def test_run_window_bad_size_exits(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    with pytest.raises(SystemExit):
        run_window(_args(size="99x"))


def test_run_window_empty_input(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    run_window(_args(size="1m"), out=out)
    assert out.getvalue() == ""

"""Integration tests: window module wired end-to-end with real parsed records."""

import json
from datetime import timedelta

from logslice.parser import parse_line
from logslice.window import aggregate_window, parse_window_expr, tumbling_windows


def _make_line(ts: str, level: str = "info", msg: str = "ok") -> str:
    return json.dumps({"timestamp": ts, "level": level, "msg": msg})


def _parse_records(lines):
    return [r for line in lines if (r := parse_line(line)) is not None]


def test_integration_three_windows():
    lines = [
        _make_line("2024-06-01T10:00:05Z", "info"),
        _make_line("2024-06-01T10:00:45Z", "warn"),
        _make_line("2024-06-01T10:01:10Z", "error"),
        _make_line("2024-06-01T10:02:30Z", "info"),
    ]
    records = _parse_records(lines)
    size = parse_window_expr("1m")
    windows = list(tumbling_windows(records, size))
    assert len(windows) == 3
    assert len(windows[0]) == 2  # 10:00:05 and 10:00:45
    assert len(windows[1]) == 1  # 10:01:10
    assert len(windows[2]) == 1  # 10:02:30


def test_integration_aggregate_all_windows():
    lines = [
        _make_line("2024-06-01T10:00:05Z"),
        _make_line("2024-06-01T10:00:55Z"),
        _make_line("2024-06-01T10:01:30Z"),
    ]
    records = _parse_records(lines)
    size = parse_window_expr("1m")
    summaries = [
        aggregate_window(w, lambda recs: {"count": len(recs)})
        for w in tumbling_windows(records, size)
    ]
    total = sum(s["count"] for s in summaries)
    assert total == 3
    for s in summaries:
        assert "window_start" in s
        assert "window_count" in s


def test_integration_30s_windows():
    lines = [
        _make_line("2024-06-01T10:00:00Z"),
        _make_line("2024-06-01T10:00:29Z"),
        _make_line("2024-06-01T10:00:31Z"),
    ]
    records = _parse_records(lines)
    size = parse_window_expr("30s")
    windows = list(tumbling_windows(records, size))
    assert len(windows) == 2
    assert len(windows[0]) == 2
    assert len(windows[1]) == 1

"""Tests for logslice.window tumbling window logic."""

from datetime import timedelta

import pytest

from logslice.window import aggregate_window, parse_window_expr, tumbling_windows


# ---------------------------------------------------------------------------
# parse_window_expr
# ---------------------------------------------------------------------------

def test_parse_seconds():
    assert parse_window_expr("30s") == timedelta(seconds=30)


def test_parse_minutes():
    assert parse_window_expr("5m") == timedelta(minutes=5)


def test_parse_hours():
    assert parse_window_expr("2h") == timedelta(hours=2)


def test_parse_days():
    assert parse_window_expr("1d") == timedelta(days=1)


def test_parse_invalid_unit():
    with pytest.raises(ValueError, match="Unknown window unit"):
        parse_window_expr("10x")


def test_parse_zero_raises():
    with pytest.raises(ValueError, match="positive"):
        parse_window_expr("0m")


def test_parse_empty_raises():
    with pytest.raises(ValueError):
        parse_window_expr("")


# ---------------------------------------------------------------------------
# tumbling_windows
# ---------------------------------------------------------------------------

def _rec(ts: str, msg: str = "hello") -> dict:
    return {"timestamp": ts, "msg": msg}


def test_tumbling_single_window():
    records = [
        _rec("2024-01-01T00:00:10Z"),
        _rec("2024-01-01T00:00:20Z"),
        _rec("2024-01-01T00:00:50Z"),
    ]
    windows = list(tumbling_windows(records, timedelta(minutes=1)))
    assert len(windows) == 1
    assert len(windows[0]) == 3


def test_tumbling_two_windows():
    records = [
        _rec("2024-01-01T00:00:10Z"),
        _rec("2024-01-01T00:01:05Z"),
    ]
    windows = list(tumbling_windows(records, timedelta(minutes=1)))
    assert len(windows) == 2


def test_tumbling_skips_no_timestamp():
    records = [{"msg": "no ts"}, _rec("2024-01-01T00:00:10Z")]
    windows = list(tumbling_windows(records, timedelta(minutes=1)))
    assert len(windows) == 1
    assert len(windows[0]) == 1


def test_tumbling_empty_input():
    windows = list(tumbling_windows([], timedelta(minutes=1)))
    assert windows == []


# ---------------------------------------------------------------------------
# aggregate_window
# ---------------------------------------------------------------------------

def test_aggregate_window_count():
    window = [_rec("2024-01-01T00:00:01Z"), _rec("2024-01-01T00:00:02Z")]
    result = aggregate_window(window, lambda recs: {"count": len(recs)})
    assert result["count"] == 2
    assert result["window_count"] == 2
    assert "window_start" in result


def test_aggregate_window_custom_start_fn():
    window = [_rec("2024-01-01T00:00:01Z")]
    result = aggregate_window(
        window,
        lambda recs: {"count": len(recs)},
        window_start_fn=lambda recs: "custom",
    )
    assert result["window_start"] == "custom"

"""Sliding/tumbling window aggregation over log records by time."""

from datetime import datetime, timedelta
from typing import Callable, Dict, Generator, Iterable, List, Optional

from logslice.timerange import extract_timestamp


def parse_window_expr(expr: str) -> timedelta:
    """Parse a window size expression like '5m', '30s', '1h' into a timedelta."""
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty window expression")
    unit = expr[-1]
    if unit not in units:
        raise ValueError(f"Unknown window unit {unit!r}; expected one of {list(units)}")
    try:
        value = int(expr[:-1])
    except ValueError:
        raise ValueError(f"Invalid window size {expr!r}")
    if value <= 0:
        raise ValueError(f"Window size must be positive, got {value}")
    return timedelta(**{units[unit]: value})


def tumbling_windows(
    records: Iterable[Dict],
    window_size: timedelta,
    ts_field: str = "timestamp",
) -> Generator[List[Dict], None, None]:
    """Yield non-overlapping tumbling windows of records grouped by time bucket."""
    current_window: List[Dict] = []
    window_start: Optional[datetime] = None

    for record in records:
        ts = extract_timestamp(record, ts_field)
        if ts is None:
            continue
        if window_start is None:
            window_start = ts
        if ts >= window_start + window_size:
            if current_window:
                yield current_window
            # Advance window_start to the correct bucket
            elapsed = int((ts - window_start) / window_size)
            window_start = window_start + window_size * elapsed
            current_window = []
        current_window.append(record)

    if current_window:
        yield current_window


def aggregate_window(
    window: List[Dict],
    agg_fn: Callable[[List[Dict]], Dict],
    window_start_fn: Optional[Callable[[List[Dict]], str]] = None,
) -> Dict:
    """Reduce a window of records to a single summary record."""
    result = agg_fn(window)
    if window_start_fn is not None:
        result["window_start"] = window_start_fn(window)
    elif window:
        ts = extract_timestamp(window[0])
        if ts is not None:
            result["window_start"] = ts.isoformat()
    result["window_count"] = len(window)
    return result

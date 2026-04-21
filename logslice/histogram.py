"""Time-bucketed histogram of log records."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from logslice.timerange import extract_timestamp


def parse_bucket_expr(expr: str) -> timedelta:
    """Parse a bucket-size expression like '1m', '5m', '1h', '30s'."""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty bucket expression")
    unit = expr[-1].lower()
    if unit not in units:
        raise ValueError(f"Unknown time unit '{unit}'. Use s, m, h, or d.")
    try:
        value = int(expr[:-1])
    except ValueError:
        raise ValueError(f"Invalid bucket size: {expr!r}")
    if value <= 0:
        raise ValueError("Bucket size must be positive")
    return timedelta(seconds=value * units[unit])


def bucket_timestamp(ts: datetime, bucket_size: timedelta) -> datetime:
    """Floor a datetime to the nearest bucket boundary."""
    epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
    total_seconds = (ts - epoch).total_seconds()
    bucket_seconds = bucket_size.total_seconds()
    floored = (total_seconds // bucket_seconds) * bucket_seconds
    return epoch + timedelta(seconds=floored)


def build_histogram(
    records: Iterable[dict],
    bucket_size: timedelta,
    ts_field: str = "timestamp",
    count_field: Optional[str] = None,
) -> List[Tuple[datetime, int]]:
    """Aggregate records into time buckets.

    Returns a sorted list of (bucket_start, count) tuples.
    If count_field is given, sum that numeric field instead of counting records.
    """
    buckets: Dict[datetime, int] = defaultdict(int)
    for record in records:
        ts = extract_timestamp(record, ts_field)
        if ts is None:
            continue
        key = bucket_timestamp(ts, bucket_size)
        if count_field:
            try:
                buckets[key] += int(record.get(count_field, 0))
            except (TypeError, ValueError):
                pass
        else:
            buckets[key] += 1
    return sorted(buckets.items())


def render_histogram(
    histogram: List[Tuple[datetime, int]],
    bar_width: int = 40,
    label_fmt: str = "%Y-%m-%dT%H:%M:%S",
) -> str:
    """Render a histogram as an ASCII bar chart string."""
    if not histogram:
        return "(no data)"
    max_count = max(count for _, count in histogram)
    lines = []
    for bucket, count in histogram:
        bar_len = int(bar_width * count / max_count) if max_count else 0
        bar = "#" * bar_len
        label = bucket.strftime(label_fmt)
        lines.append(f"{label} | {bar:<{bar_width}} {count}")
    return "\n".join(lines)

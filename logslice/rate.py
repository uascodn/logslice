"""Compute per-time-bucket event rates from structured log records."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Iterator

from logslice.timerange import extract_timestamp
from logslice.window import parse_window_expr


def parse_rate_expr(expr: str) -> dict:
    """Parse a rate expression like '1m' or '30s:level'.

    Returns a dict with keys:
        bucket_seconds  – window size in seconds
        group_by        – field name to group by, or None
    """
    parts = expr.strip().split(":")
    if len(parts) > 2:
        raise ValueError(f"Invalid rate expression: {expr!r}")
    bucket_seconds = parse_window_expr(parts[0])
    group_by = parts[1].strip() if len(parts) == 2 and parts[1].strip() else None
    return {"bucket_seconds": bucket_seconds, "group_by": group_by}


def compute_rate(
    records: Iterable[dict],
    bucket_seconds: int,
    group_by: str | None = None,
) -> Iterator[dict]:
    """Yield one summary record per (bucket, group) combination.

    Each yielded record contains:
        bucket_start  – ISO timestamp of the bucket start (seconds precision)
        group         – group value (only present when group_by is set)
        count         – number of log lines in this bucket
        rate_per_sec  – count / bucket_seconds
    """
    # bucket_key -> group_key -> count
    buckets: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for rec in records:
        ts = extract_timestamp(rec)
        if ts is None:
            continue
        epoch = ts.timestamp()
        bucket_key = int(epoch // bucket_seconds) * bucket_seconds
        group_val = str(rec.get(group_by, "")) if group_by else ""
        buckets[bucket_key][group_val] += 1

    for bucket_key in sorted(buckets):
        from datetime import datetime, timezone

        bucket_start = datetime.fromtimestamp(bucket_key, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        for group_val, count in sorted(buckets[bucket_key].items()):
            record: dict = {
                "bucket_start": bucket_start,
                "count": count,
                "rate_per_sec": round(count / bucket_seconds, 6),
            }
            if group_by:
                record["group"] = group_val
            yield record

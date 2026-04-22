"""Resample time-series log records into fixed-size time buckets."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.timerange import extract_timestamp

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_resample_expr(expr: str) -> Tuple[int, str]:
    """Parse a resample expression like '5m:count' or '1h:avg:latency'.

    Returns (bucket_seconds, agg_spec) where agg_spec is the remainder
    after the bucket size, e.g. 'count', 'avg:latency', 'sum:bytes'.
    """
    parts = expr.split(":", 1)
    if len(parts) < 2:
        raise ValueError(f"resample expression must be '<interval>:<agg>[:<field>]', got: {expr!r}")
    interval_str, agg_spec = parts[0].strip(), parts[1].strip()
    m = re.fullmatch(r"(\d+)([smhd])", interval_str)
    if not m:
        raise ValueError(f"invalid interval {interval_str!r}; expected e.g. '30s', '5m', '1h'")
    bucket_seconds = int(m.group(1)) * _UNIT_SECONDS[m.group(2)]
    if bucket_seconds <= 0:
        raise ValueError("interval must be positive")
    return bucket_seconds, agg_spec


def _bucket_key(ts: datetime, bucket_seconds: int) -> datetime:
    epoch = ts.timestamp()
    floored = int(epoch // bucket_seconds) * bucket_seconds
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def resample_records(
    records: Iterable[dict],
    bucket_seconds: int,
    agg: str,
    field: Optional[str] = None,
) -> List[dict]:
    """Group records into time buckets and aggregate.

    agg: 'count', 'sum', 'avg', 'min', 'max'
    field: required for sum/avg/min/max
    """
    agg = agg.lower()
    if agg != "count" and field is None:
        raise ValueError(f"agg '{agg}' requires a field name")

    buckets: Dict[datetime, List] = defaultdict(list)
    for rec in records:
        ts = extract_timestamp(rec)
        if ts is None:
            continue
        key = _bucket_key(ts, bucket_seconds)
        value = rec.get(field) if field else 1
        try:
            buckets[key].append(float(value) if value is not None else None)
        except (TypeError, ValueError):
            pass

    results = []
    for bucket_ts in sorted(buckets):
        values = [v for v in buckets[bucket_ts] if v is not None]
        if agg == "count":
            agg_value = len(buckets[bucket_ts])
        elif agg == "sum":
            agg_value = sum(values)
        elif agg == "avg":
            agg_value = sum(values) / len(values) if values else None
        elif agg == "min":
            agg_value = min(values) if values else None
        elif agg == "max":
            agg_value = max(values) if values else None
        else:
            raise ValueError(f"unknown aggregation: {agg!r}")
        results.append({
            "bucket": bucket_ts.isoformat(),
            "agg": agg,
            "field": field,
            "value": agg_value,
            "count": len(buckets[bucket_ts]),
        })
    return results

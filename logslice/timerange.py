"""Time range parsing and filtering for logslice."""

from datetime import datetime, timezone
from typing import Optional, Tuple

TIME_FIELDS = ("time", "timestamp", "ts", "@timestamp", "date")

DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def parse_datetime(value: str) -> Optional[datetime]:
    """Try to parse a datetime string using known formats."""
    for fmt in DATETIME_FORMATS:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def extract_timestamp(record: dict) -> Optional[datetime]:
    """Extract a datetime from a log record by checking known time fields."""
    for field in TIME_FIELDS:
        if field in record:
            result = parse_datetime(str(record[field]))
            if result is not None:
                return result
    return None


def in_time_range(
    record: dict,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> bool:
    """Return True if the record's timestamp falls within [start, end]."""
    if start is None and end is None:
        return True
    ts = extract_timestamp(record)
    if ts is None:
        return False
    if start is not None and ts < start:
        return False
    if end is not None and ts > end:
        return False
    return True


def parse_time_range(start_str: Optional[str], end_str: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse start and end strings into datetime objects."""
    start = parse_datetime(start_str) if start_str else None
    end = parse_datetime(end_str) if end_str else None
    if start_str and start is None:
        raise ValueError(f"Could not parse start time: {start_str!r}")
    if end_str and end is None:
        raise ValueError(f"Could not parse end time: {end_str!r}")
    return start, end

"""High-level log slicing: combines parsing, filtering, and time range."""

from datetime import datetime
from typing import Iterable, Iterator, Optional, List, Dict, Any

from logslice.parser import parse_line
from logslice.filter import apply_filters, parse_filter_expr
from logslice.timerange import in_time_range, parse_time_range


def slice_lines(
    lines: Iterable[str],
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
    filter_exprs: Optional[List[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Parse and filter an iterable of log lines.

    Args:
        lines: raw log lines (JSON or logfmt)
        start_str: optional ISO start time string
        end_str: optional ISO end time string
        filter_exprs: list of filter expressions like 'level=error'

    Yields:
        Parsed log records matching all criteria.
    """
    start, end = parse_time_range(start_str, end_str)
    filters = [parse_filter_expr(e) for e in (filter_exprs or [])]

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        record = parse_line(line)
        if record is None:
            continue
        if not in_time_range(record, start, end):
            continue
        if not apply_filters(record, filters):
            continue
        yield record


def slice_file(
    path: str,
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
    filter_exprs: Optional[List[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """Open a log file and yield matching records."""
    with open(path, "r", encoding="utf-8") as fh:
        yield from slice_lines(fh, start_str, end_str, filter_exprs)

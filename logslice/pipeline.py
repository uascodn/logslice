"""High-level pipeline that wires parser, filter, timerange, dedupe, and output."""

from typing import Iterator, Optional, List, TextIO

from logslice.parser import parse_line
from logslice.filter import apply_filters, parse_filter_expr
from logslice.timerange import in_time_range, parse_time_range
from logslice.dedupe import dedupe_records, dedupe_consecutive
from logslice.output import format_record


def build_pipeline(
    lines: Iterator[str],
    *,
    time_range: Optional[str] = None,
    filters: Optional[List[str]] = None,
    dedupe: bool = False,
    dedupe_consecutive: bool = False,
    dedupe_fields: Optional[List[str]] = None,
    output_format: str = "json",
) -> Iterator[str]:
    """
    Parse, filter, deduplicate, and format log lines.

    Args:
        lines: raw text lines from a log source
        time_range: optional string like "2024-01-01/2024-01-02"
        filters: list of filter expressions like "level=error"
        dedupe: if True, remove globally duplicate records
        dedupe_consecutive: if True, remove consecutive duplicate records
        dedupe_fields: fields to use for deduplication key
        output_format: one of "json", "logfmt", "pretty"

    Yields:
        Formatted output strings (one per matching record)
    """
    parsed = (parse_line(line) for line in lines)
    records = (r for r in parsed if r is not None)

    if time_range:
        start, end = parse_time_range(time_range)
        records = (r for r in records if in_time_range(r, start, end))

    if filters:
        exprs = [parse_filter_expr(f) for f in filters]
        records = (r for r in records if apply_filters(r, exprs))

    if dedupe:
        records = dedupe_records(records, fields=dedupe_fields)
    elif dedupe_consecutive:
        from logslice import dedupe as _dedupe_mod
        records = _dedupe_mod.dedupe_consecutive(records, fields=dedupe_fields)

    for record in records:
        yield format_record(record, output_format)


def run_pipeline(
    infile: TextIO,
    outfile: TextIO,
    **kwargs,
) -> int:
    """
    Run the pipeline from a file-like input to a file-like output.

    Returns:
        Number of records written.
    """
    lines = (line.rstrip("\n") for line in infile)
    count = 0
    for formatted in build_pipeline(lines, **kwargs):
        outfile.write(formatted + "\n")
        count += 1
    return count

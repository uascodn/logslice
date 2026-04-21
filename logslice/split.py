"""Split log records into multiple output files based on a field value."""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.parser import parse_line


def parse_split_expr(expr: str) -> Tuple[str, Optional[str]]:
    """Parse a split expression like 'field' or 'field:prefix'.

    Returns (field_name, output_prefix).
    output_prefix may be None if not specified.
    """
    if ":" in expr:
        field, prefix = expr.split(":", 1)
        return field.strip(), prefix.strip() or None
    return expr.strip(), None


def group_records(
    records: Iterable[dict],
    field: str,
    default: str = "__unknown__",
) -> Dict[str, List[dict]]:
    """Group records by the value of *field*.

    Records that are missing *field* are grouped under *default*.
    """
    groups: Dict[str, List[dict]] = defaultdict(list)
    for record in records:
        key = str(record.get(field, default))
        groups[key].append(record)
    return dict(groups)


def split_to_files(
    records: Iterable[dict],
    field: str,
    output_dir: str,
    prefix: Optional[str] = None,
    suffix: str = ".jsonl",
    default: str = "__unknown__",
) -> Dict[str, int]:
    """Write records into per-value files inside *output_dir*.

    Files are named ``<prefix><value><suffix>``.  Returns a mapping of
    field-value -> number of records written.
    """
    import json

    os.makedirs(output_dir, exist_ok=True)
    counts: Dict[str, int] = defaultdict(int)
    handles: Dict[str, object] = {}

    try:
        for record in records:
            key = str(record.get(field, default))
            if key not in handles:
                file_prefix = f"{prefix}_" if prefix else ""
                filename = os.path.join(output_dir, f"{file_prefix}{key}{suffix}")
                handles[key] = open(filename, "w", encoding="utf-8")  # noqa: WPS515
            handles[key].write(json.dumps(record) + "\n")  # type: ignore[union-attr]
            counts[key] += 1
    finally:
        for fh in handles.values():
            fh.close()  # type: ignore[union-attr]

    return dict(counts)


def iter_split_groups(
    lines: Iterable[str],
    field: str,
    default: str = "__unknown__",
) -> Iterator[Tuple[str, dict]]:
    """Yield (group_key, record) pairs parsed from raw log *lines*."""
    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        record = parse_line(line)
        if record is None:
            continue
        key = str(record.get(field, default))
        yield key, record

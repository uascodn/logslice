"""Deduplication of log records based on field values or message similarity."""

from typing import Iterator, Optional, List
from collections import OrderedDict


def _record_key(record: dict, fields: List[str]) -> tuple:
    """Build a hashable key from selected fields of a record."""
    return tuple(str(record.get(f, "")) for f in fields)


def dedupe_records(
    records: Iterator[dict],
    fields: Optional[List[str]] = None,
    max_seen: int = 10_000,
) -> Iterator[dict]:
    """
    Yield records, skipping duplicates based on the given fields.

    Args:
        records: iterable of parsed log record dicts
        fields: list of field names to use as the dedup key;
                defaults to ["msg"] if None
        max_seen: maximum number of keys to remember (LRU eviction)
    """
    if fields is None:
        fields = ["msg"]

    seen: OrderedDict = OrderedDict()

    for record in records:
        key = _record_key(record, fields)
        if key in seen:
            seen.move_to_end(key)
            continue
        seen[key] = True
        if len(seen) > max_seen:
            seen.popitem(last=False)
        yield record


def dedupe_consecutive(
    records: Iterator[dict],
    fields: Optional[List[str]] = None,
) -> Iterator[dict]:
    """
    Yield records, skipping consecutive duplicates only.

    Args:
        records: iterable of parsed log record dicts
        fields: list of field names to use as the dedup key;
                defaults to ["msg"] if None
    """
    if fields is None:
        fields = ["msg"]

    last_key = None
    for record in records:
        key = _record_key(record, fields)
        if key == last_key:
            continue
        last_key = key
        yield record

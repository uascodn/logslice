"""unique.py — deduplicate records by one or more field values.

Provides streaming and batch uniqueness filtering, with support for
choosing which fields define identity and a configurable keep-first
vs keep-last strategy.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, Iterator, List, Optional


def _make_key(record: dict, fields: List[str]) -> tuple:
    """Return a hashable key from the given fields of *record*.

    Missing fields contribute ``None`` to the key so that records with
    absent fields are still grouped correctly.
    """
    return tuple(record.get(f) for f in fields)


def unique_records(
    records: Iterable[dict],
    fields: List[str],
    keep: str = "first",
) -> Iterator[dict]:
    """Yield records that are unique with respect to *fields*.

    Parameters
    ----------
    records:
        Input stream of parsed log records.
    fields:
        Field names whose combined value defines record identity.
    keep:
        ``"first"`` (default) keeps the earliest occurrence;
        ``"last"`` keeps the latest occurrence.

    Yields
    ------
    dict
        Unique records in their original order (for ``keep="first"``) or
        in original order with earlier duplicates replaced (``keep="last"``).
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    if keep == "first":
        seen: set = set()
        for rec in records:
            key = _make_key(rec, fields)
            if key not in seen:
                seen.add(key)
                yield rec
    else:  # keep == "last"
        # Collect all records, then emit only the last occurrence of each key
        # while preserving the position of the *last* occurrence.
        # We use an OrderedDict keyed by identity to track position.
        ordered: OrderedDict[tuple, dict] = OrderedDict()
        for rec in records:
            key = _make_key(rec, fields)
            if key in ordered:
                # Move to end to reflect latest position
                ordered.move_to_end(key)
            ordered[key] = rec
        yield from ordered.values()


def parse_unique_expr(expr: str) -> List[str]:
    """Parse a comma-separated list of field names.

    Example
    -------
    >>> parse_unique_expr("service,host")
    ['service', 'host']
    """
    fields = [f.strip() for f in expr.split(",") if f.strip()]
    if not fields:
        raise ValueError(f"unique expression must contain at least one field: {expr!r}")
    return fields


def apply_unique(
    records: Iterable[dict],
    expr: Optional[str],
    keep: str = "first",
) -> Iterator[dict]:
    """Convenience wrapper: parse *expr* and apply uniqueness filter.

    If *expr* is ``None`` or empty the records are yielded unchanged.
    """
    if not expr:
        yield from records
        return
    fields = parse_unique_expr(expr)
    yield from unique_records(records, fields, keep=keep)

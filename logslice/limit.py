"""Limit and offset support for log record streams."""
from __future__ import annotations

from typing import Iterable, Iterator


def parse_limit_expr(expr: str) -> dict:
    """Parse a limit expression like '100' or '50:200' (offset:limit).

    Returns a dict with keys 'offset' and 'limit'.
    """
    expr = expr.strip()
    if ":" in expr:
        parts = expr.split(":", 1)
        try:
            offset = int(parts[0])
            limit = int(parts[1])
        except ValueError:
            raise ValueError(f"Invalid limit expression: {expr!r}. Expected 'N' or 'offset:N'.")
    else:
        try:
            offset = 0
            limit = int(expr)
        except ValueError:
            raise ValueError(f"Invalid limit expression: {expr!r}. Expected an integer.")

    if limit < 0:
        raise ValueError(f"Limit must be non-negative, got {limit}.")
    if offset < 0:
        raise ValueError(f"Offset must be non-negative, got {offset}.")

    return {"offset": offset, "limit": limit}


def limit_records(
    records: Iterable[dict],
    limit: int,
    offset: int = 0,
) -> Iterator[dict]:
    """Yield at most *limit* records after skipping *offset* records."""
    if limit == 0:
        return
    skipped = 0
    emitted = 0
    for record in records:
        if skipped < offset:
            skipped += 1
            continue
        yield record
        emitted += 1
        if emitted >= limit:
            break


def apply_limit(records: Iterable[dict], expr: str) -> Iterator[dict]:
    """Parse *expr* and apply limit/offset to *records*."""
    params = parse_limit_expr(expr)
    return limit_records(records, limit=params["limit"], offset=params["offset"])

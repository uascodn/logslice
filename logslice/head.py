"""head.py — return the first N records from a stream."""

from __future__ import annotations

from typing import Iterable, Iterator


def first_n_records(records: Iterable[dict], n: int) -> list[dict]:
    """Return up to *n* records from *records*."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    result: list[dict] = []
    for record in records:
        if len(result) >= n:
            break
        result.append(record)
    return result


def head_records(records: Iterable[dict], n: int) -> Iterator[dict]:
    """Yield up to *n* records from *records* (lazy iterator variant)."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    count = 0
    for record in records:
        if count >= n:
            return
        yield record
        count += 1


def parse_head_expr(expr: str) -> int:
    """Parse a head expression like '10' or 'n=10' and return n as int."""
    expr = expr.strip()
    if expr.startswith("n="):
        expr = expr[2:]
    try:
        value = int(expr)
    except ValueError:
        raise ValueError(f"Invalid head expression: {expr!r}. Expected an integer.")
    if value < 0:
        raise ValueError(f"Head count must be >= 0, got {value}")
    return value

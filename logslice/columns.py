"""Column selection and reordering for log records."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


def parse_columns_expr(expr: str) -> List[str]:
    """Parse a comma-separated list of column names.

    Example: "level,msg,service" -> ["level", "msg", "service"]
    """
    if not expr or not expr.strip():
        raise ValueError("columns expression must not be empty")
    cols = [c.strip() for c in expr.split(",")]
    if any(c == "" for c in cols):
        raise ValueError(f"invalid columns expression: {expr!r}")
    return cols


def select_columns(
    record: Dict[str, Any],
    columns: List[str],
    fill: Optional[Any] = None,
) -> Dict[str, Any]:
    """Return a new record containing only *columns*, in that order.

    Missing fields are set to *fill* (default ``None``).
    """
    return {col: record.get(col, fill) for col in columns}


def reorder_columns(
    record: Dict[str, Any],
    columns: List[str],
) -> Dict[str, Any]:
    """Return a new record with *columns* first, remaining keys appended.

    Keys in *columns* that are absent from *record* are skipped.
    """
    result: Dict[str, Any] = {}
    for col in columns:
        if col in record:
            result[col] = record[col]
    for key, value in record.items():
        if key not in result:
            result[key] = value
    return result


def apply_columns(
    records: Iterable[Dict[str, Any]],
    columns: List[str],
    strict: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Yield records with only *columns* retained.

    When *strict* is True, missing columns raise ``KeyError``.
    """
    for record in records:
        if strict:
            yield {col: record[col] for col in columns}
        else:
            yield select_columns(record, columns)

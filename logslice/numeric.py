"""Numeric field filtering: range checks and threshold comparisons."""

from typing import Any, Dict, Iterator, Optional, Tuple


def _to_float(value: Any) -> Optional[float]:
    """Attempt to convert a value to float; return None on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def numeric_in_range(
    record: Dict[str, Any],
    field: str,
    low: Optional[float],
    high: Optional[float],
) -> bool:
    """Return True if record[field] is within [low, high] (inclusive, open-ended if None)."""
    raw = record.get(field)
    if raw is None:
        return False
    value = _to_float(raw)
    if value is None:
        return False
    if low is not None and value < low:
        return False
    if high is not None and value > high:
        return False
    return True


def numeric_threshold(
    record: Dict[str, Any],
    field: str,
    op: str,
    threshold: float,
) -> bool:
    """Return True if record[field] satisfies the comparison op against threshold.

    Supported ops: '>', '>=', '<', '<=', '==', '!='.
    """
    raw = record.get(field)
    if raw is None:
        return False
    value = _to_float(raw)
    if value is None:
        return False
    ops = {
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    fn = ops.get(op)
    if fn is None:
        raise ValueError(f"Unsupported numeric operator: {op!r}")
    return fn(value, threshold)


def parse_numeric_expr(expr: str) -> Tuple[str, str, float]:
    """Parse an expression like 'latency>100' or 'status_code==200'.

    Returns (field, op, threshold).
    """
    for op in (">=", "<=", "!=", "==", ">", "<"):
        if op in expr:
            parts = expr.split(op, 1)
            field = parts[0].strip()
            raw_val = parts[1].strip()
            if not field:
                raise ValueError(f"Missing field name in numeric expression: {expr!r}")
            try:
                threshold = float(raw_val)
            except ValueError:
                raise ValueError(
                    f"Invalid numeric threshold {raw_val!r} in expression: {expr!r}"
                )
            return field, op, threshold
    raise ValueError(f"No valid operator found in numeric expression: {expr!r}")


def apply_numeric_filter(
    records: Iterator[Dict[str, Any]],
    field: str,
    op: str,
    threshold: float,
) -> Iterator[Dict[str, Any]]:
    """Yield only records where field satisfies the numeric comparison."""
    for record in records:
        if numeric_threshold(record, field, op, threshold):
            yield record

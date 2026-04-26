"""Field value normalization: trim whitespace, lowercase, uppercase, titlecase."""

from typing import Any, Dict, List


_MODES = ("lower", "upper", "title", "strip")


def normalize_value(value: Any, mode: str) -> Any:
    """Apply a normalization mode to a single value.

    Non-string values are returned unchanged.
    """
    if not isinstance(value, str):
        return value
    if mode == "lower":
        return value.lower()
    if mode == "upper":
        return value.upper()
    if mode == "title":
        return value.title()
    if mode == "strip":
        return value.strip()
    raise ValueError(f"Unknown normalization mode: {mode!r}. Choose from {_MODES}.")


def normalize_field(record: Dict[str, Any], field: str, mode: str) -> Dict[str, Any]:
    """Return a new record with *field* normalized using *mode*."""
    if field not in record:
        return record
    result = dict(record)
    result[field] = normalize_value(record[field], mode)
    return result


def normalize_fields(
    record: Dict[str, Any], steps: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Apply multiple normalization steps sequentially.

    Each step is a dict with keys ``field`` and ``mode``.
    """
    for step in steps:
        record = normalize_field(record, step["field"], step["mode"])
    return record


def parse_normalize_expr(expr: str) -> Dict[str, str]:
    """Parse a normalization expression of the form ``field:mode``.

    Returns a dict with ``field`` and ``mode`` keys.

    >>> parse_normalize_expr("level:lower")
    {'field': 'level', 'mode': 'lower'}
    """
    expr = expr.strip()
    if ":" not in expr:
        raise ValueError(
            f"Invalid normalize expression {expr!r}. Expected 'field:mode'."
        )
    field, _, mode = expr.partition(":")
    field = field.strip()
    mode = mode.strip()
    if not field:
        raise ValueError("Field name must not be empty.")
    if mode not in _MODES:
        raise ValueError(
            f"Unknown mode {mode!r} in expression {expr!r}. Choose from {_MODES}."
        )
    return {"field": field, "mode": mode}


def apply_normalizations(
    record: Dict[str, Any], exprs: List[str]
) -> Dict[str, Any]:
    """Parse and apply a list of normalization expression strings to *record*."""
    steps = [parse_normalize_expr(e) for e in exprs]
    return normalize_fields(record, steps)

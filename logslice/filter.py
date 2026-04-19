"""Field-based filtering for parsed log records."""

from typing import Any, Optional


def field_matches(record: dict, field: str, value: Any) -> bool:
    """Return True if record[field] equals value (string comparison)."""
    if field not in record:
        return False
    return str(record[field]) == str(value)


def field_contains(record: dict, field: str, substring: str) -> bool:
    """Return True if record[field] contains the given substring."""
    if field not in record:
        return False
    return substring in str(record[field])


def apply_filters(record: dict, filters: list[tuple[str, str, str]]) -> bool:
    """Apply a list of filter tuples (field, op, value) to a record.

    Supported ops: '=', '!=', 'contains'
    All filters must match (AND logic).
    """
    for field, op, value in filters:
        if op == "=":
            if not field_matches(record, field, value):
                return False
        elif op == "!=":
            if field_matches(record, field, value):
                return False
        elif op == "contains":
            if not field_contains(record, field, value):
                return False
        else:
            raise ValueError(f"Unsupported filter operator: {op!r}")
    return True


def parse_filter_expr(expr: str) -> tuple[str, str, str]:
    """Parse a filter expression string like 'level=error' or 'msg contains foo'."""
    for op in ("!=", "=", " contains "):
        if op in expr:
            parts = expr.split(op, 1)
            return parts[0].strip(), op.strip(), parts[1].strip()
    raise ValueError(f"Cannot parse filter expression: {expr!r}")

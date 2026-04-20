"""Sort log records by a field value."""
from typing import List, Dict, Any, Optional


def sort_records(
    records: List[Dict[str, Any]],
    field: str,
    reverse: bool = False,
    missing_last: bool = True,
) -> List[Dict[str, Any]]:
    """Sort records by the given field.

    Args:
        records: list of parsed log records.
        field: field name to sort by.
        reverse: if True, sort descending.
        missing_last: if True, records missing the field appear at the end.
    """
    sentinel_high = "\xff" * 8
    sentinel_low = ""

    def key(record: Dict[str, Any]):
        value = record.get(field)
        if value is None:
            placeholder = sentinel_high if missing_last else sentinel_low
            return (1, placeholder)
        return (0, str(value))

    return sorted(records, key=key, reverse=reverse)


def parse_sort_expr(expr: str):
    """Parse a sort expression of the form 'field[:asc|:desc]'.

    Returns (field, reverse) tuple.

    Examples:
        'timestamp'       -> ('timestamp', False)
        'timestamp:asc'   -> ('timestamp', False)
        'timestamp:desc'  -> ('timestamp', True)
    """
    parts = expr.split(":")
    field = parts[0].strip()
    if not field:
        raise ValueError(f"Invalid sort expression: {expr!r}")
    direction = parts[1].strip().lower() if len(parts) > 1 else "asc"
    if direction not in ("asc", "desc"):
        raise ValueError(f"Sort direction must be 'asc' or 'desc', got {direction!r}")
    return field, direction == "desc"

"""Field value truncation utilities for logslice output."""

from typing import Optional

DEFAULT_MAX_LENGTH = 200


def truncate_value(value: str, max_length: int = DEFAULT_MAX_LENGTH, suffix: str = "...") -> str:
    """Truncate a string value to max_length, appending suffix if truncated."""
    if len(value) <= max_length:
        return value
    return value[:max_length - len(suffix)] + suffix


def truncate_field(record: dict, field: str, max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """Return a copy of record with the specified field truncated."""
    record = dict(record)
    if field in record and isinstance(record[field], str):
        record[field] = truncate_value(record[field], max_length)
    return record


def truncate_fields(record: dict, fields: list, max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """Return a copy of record with all listed fields truncated."""
    record = dict(record)
    for field in fields:
        if field in record and isinstance(record[field], str):
            record[field] = truncate_value(record[field], max_length)
    return record


def truncate_all_fields(record: dict, max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """Return a copy of record with every string field truncated."""
    return {
        k: truncate_value(v, max_length) if isinstance(v, str) else v
        for k, v in record.items()
    }


def parse_truncate_expr(expr: str) -> tuple:
    """Parse 'field:max_length' or just 'max_length' expression.

    Returns (field_or_none, max_length).
    """
    if ":" in expr:
        field, _, length_str = expr.partition(":")
        try:
            return field.strip(), int(length_str.strip())
        except ValueError:
            raise ValueError(f"Invalid truncate expression: {expr!r}")
    else:
        try:
            return None, int(expr.strip())
        except ValueError:
            raise ValueError(f"Invalid truncate expression: {expr!r}")

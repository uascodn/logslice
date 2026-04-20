"""Field masking and redaction utilities for sensitive log data."""

import re
from typing import Any

_MASK_CHAR = "*"
_DEFAULT_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "token": re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),
}


def mask_value(value: str, char: str = _MASK_CHAR, keep: int = 0) -> str:
    """Mask a string value, optionally keeping the last `keep` characters."""
    if not isinstance(value, str):
        return value
    if keep > 0 and len(value) > keep:
        return char * (len(value) - keep) + value[-keep:]
    return char * len(value)


def mask_field(record: dict, field: str, char: str = _MASK_CHAR, keep: int = 0) -> dict:
    """Return a copy of record with the specified field masked."""
    record = dict(record)
    if field in record:
        record[field] = mask_value(str(record[field]), char=char, keep=keep)
    return record


def mask_fields(record: dict, fields: list[str], char: str = _MASK_CHAR, keep: int = 0) -> dict:
    """Mask multiple fields in a record."""
    for field in fields:
        record = mask_field(record, field, char=char, keep=keep)
    return record


def redact_patterns(record: dict, pattern_names: list[str] | None = None) -> dict:
    """Replace known sensitive patterns (email, ip, token) with [REDACTED]."""
    patterns = (
        {k: _DEFAULT_PATTERNS[k] for k in pattern_names if k in _DEFAULT_PATTERNS}
        if pattern_names
        else _DEFAULT_PATTERNS
    )
    record = dict(record)
    for key, value in record.items():
        if isinstance(value, str):
            for _name, pat in patterns.items():
                value = pat.sub("[REDACTED]", value)
            record[key] = value
    return record


def parse_mask_expr(expr: str) -> dict:
    """Parse a mask expression like 'field:keep=4' or 'field'."""
    parts = expr.split(":")
    field = parts[0].strip()
    keep = 0
    char = _MASK_CHAR
    for part in parts[1:]:
        if part.startswith("keep="):
            keep = int(part.split("=", 1)[1])
        elif part.startswith("char="):
            char = part.split("=", 1)[1]
    return {"field": field, "keep": keep, "char": char}

"""Full-text and field-level pattern search across log records."""

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional


def _field_value_str(value: Any) -> str:
    """Convert a field value to a searchable string."""
    if isinstance(value, str):
        return value
    return str(value)


def grep_record(
    record: Dict[str, Any],
    pattern: re.Pattern,
    fields: Optional[List[str]] = None,
) -> bool:
    """Return True if *pattern* matches any (or specified) field in *record*."""
    targets = fields if fields else list(record.keys())
    for key in targets:
        if key not in record:
            continue
        if pattern.search(_field_value_str(record[key])):
            return True
    return False


def grep_records(
    records: Iterable[Dict[str, Any]],
    pattern: re.Pattern,
    fields: Optional[List[str]] = None,
    invert: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Yield records that match (or don't match when *invert* is True)."""
    for record in records:
        matched = grep_record(record, pattern, fields=fields)
        if matched ^ invert:
            yield record


def parse_grep_expr(expr: str) -> Dict[str, Any]:
    """Parse a grep expression string into keyword arguments for grep_records.

    Supported formats:
        ``/pattern/``           – case-sensitive regex
        ``/pattern/i``          – case-insensitive regex
        ``field:/pattern/``     – search only *field*
        ``field:/pattern/i``    – case-insensitive, single field
    """
    field: Optional[str] = None
    flags = 0

    # Optional leading field name
    field_match = re.match(r'^([\w.]+):(.+)$', expr, re.DOTALL)
    if field_match:
        field = field_match.group(1)
        expr = field_match.group(2)

    # Regex literal  /pattern/  or  /pattern/i
    literal = re.match(r'^/(.+)/([i]*)$', expr, re.DOTALL)
    if literal:
        raw_pattern = literal.group(1)
        modifiers = literal.group(2)
        if 'i' in modifiers:
            flags |= re.IGNORECASE
    else:
        # Treat plain string as a literal substring search (escaped)
        raw_pattern = re.escape(expr)

    compiled = re.compile(raw_pattern, flags)
    return {
        'pattern': compiled,
        'fields': [field] if field else None,
    }

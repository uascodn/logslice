"""Extract a sub-field or regex capture group into a new field."""

import re
from typing import Any, Dict, List, Optional, Tuple


def extract_regex(
    record: Dict[str, Any],
    source_field: str,
    pattern: str,
    dest_field: str,
    group: int = 1,
) -> Dict[str, Any]:
    """Extract a regex capture group from source_field into dest_field."""
    value = record.get(source_field)
    if value is None:
        return record
    m = re.search(pattern, str(value))
    if m:
        try:
            captured = m.group(group)
        except IndexError:
            captured = m.group(0)
        return {**record, dest_field: captured}
    return record


def extract_split(
    record: Dict[str, Any],
    source_field: str,
    delimiter: str,
    index: int,
    dest_field: str,
) -> Dict[str, Any]:
    """Split source_field by delimiter and store the part at index in dest_field."""
    value = record.get(source_field)
    if value is None:
        return record
    parts = str(value).split(delimiter)
    if 0 <= index < len(parts):
        return {**record, dest_field: parts[index]}
    return record


def parse_extract_expr(expr: str) -> Dict[str, Any]:
    """Parse an extract expression.

    Formats:
      regex:<src>/<pattern>/<dest>[/<group>]   e.g. regex:msg/error (\\d+)/code/1
      split:<src>/<delimiter>/<index>/<dest>   e.g. split:path/./2/filename
    """
    if expr.startswith("regex:"):
        rest = expr[len("regex:"):]
        parts = rest.split("/", 3)
        if len(parts) < 3:
            raise ValueError(f"Invalid regex extract expression: {expr!r}")
        src, pattern, dest = parts[0], parts[1], parts[2]
        group = int(parts[3]) if len(parts) == 4 else 1
        return {"mode": "regex", "source": src, "pattern": pattern, "dest": dest, "group": group}
    elif expr.startswith("split:"):
        rest = expr[len("split:"):]
        parts = rest.split("/", 3)
        if len(parts) != 4:
            raise ValueError(f"Invalid split extract expression: {expr!r}")
        src, delimiter, index_str, dest = parts
        return {"mode": "split", "source": src, "delimiter": delimiter, "index": int(index_str), "dest": dest}
    else:
        raise ValueError(f"Unknown extract mode in expression: {expr!r}")


def apply_extracts(record: Dict[str, Any], exprs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply a list of parsed extract expressions to a record."""
    for e in exprs:
        if e["mode"] == "regex":
            record = extract_regex(record, e["source"], e["pattern"], e["dest"], e["group"])
        elif e["mode"] == "split":
            record = extract_split(record, e["source"], e["delimiter"], e["index"], e["dest"])
    return record

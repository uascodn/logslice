"""Field-level diff utilities for comparing individual log records."""

from typing import Any, Dict, List, Tuple

ADDED = "added"
REMOVED = "removed"
CHANGED = "changed"
UNCHANGED = "unchanged"


def diff_records(
    a: Dict[str, Any],
    b: Dict[str, Any],
    ignore_fields: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """Return a list of field-level diff entries between two records.

    Each entry has: field, status, old_value, new_value.
    """
    ignore = set(ignore_fields or [])
    all_keys = (set(a) | set(b)) - ignore
    result = []
    for key in sorted(all_keys):
        if key in a and key not in b:
            result.append({"field": key, "status": REMOVED, "old": a[key], "new": None})
        elif key not in a and key in b:
            result.append({"field": key, "status": ADDED, "old": None, "new": b[key]})
        elif a[key] != b[key]:
            result.append({"field": key, "status": CHANGED, "old": a[key], "new": b[key]})
        else:
            result.append({"field": key, "status": UNCHANGED, "old": a[key], "new": b[key]})
    return result


def has_changes(diff: List[Dict[str, Any]]) -> bool:
    """Return True if any diff entry is not UNCHANGED."""
    return any(entry["status"] != UNCHANGED for entry in diff)


def diff_summary(diff: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return counts per status in the diff."""
    counts: Dict[str, int] = {ADDED: 0, REMOVED: 0, CHANGED: 0, UNCHANGED: 0}
    for entry in diff:
        counts[entry["status"]] += 1
    return counts


def render_diff(diff: List[Dict[str, Any]], color: bool = False) -> str:
    """Render a human-readable diff string."""
    lines = []
    for entry in diff:
        status = entry["status"]
        field = entry["field"]
        if status == UNCHANGED:
            continue
        elif status == ADDED:
            line = f"  + {field}: {entry['new']!r}"
            lines.append(_maybe_color(line, "\033[32m", color))
        elif status == REMOVED:
            line = f"  - {field}: {entry['old']!r}"
            lines.append(_maybe_color(line, "\033[31m", color))
        elif status == CHANGED:
            line = f"  ~ {field}: {entry['old']!r} -> {entry['new']!r}"
            lines.append(_maybe_color(line, "\033[33m", color))
    return "\n".join(lines) if lines else "  (no changes)"


def _maybe_color(text: str, code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{code}{text}\033[0m"

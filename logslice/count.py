"""Field value counting utilities for logslice."""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Iterator


def parse_count_expr(expr: str) -> dict:
    """Parse a count expression like 'field' or 'field:top=20'.

    Returns a dict with keys: field, top.
    """
    parts = expr.split(":")
    field = parts[0].strip()
    if not field:
        raise ValueError("count expression must specify a field name")

    top = 10
    for part in parts[1:]:
        if part.startswith("top="):
            try:
                top = int(part[4:])
            except ValueError:
                raise ValueError(f"invalid top value in count expression: {part!r}")

    return {"field": field, "top": top}


def count_field_values(
    records: Iterable[dict],
    field: str,
) -> Counter:
    """Count occurrences of each value for *field* across *records*."""
    counter: Counter = Counter()
    for record in records:
        value = record.get(field)
        if value is not None:
            counter[str(value)] += 1
    return counter


def top_counts(
    counter: Counter,
    top: int = 10,
) -> list[tuple[str, int]]:
    """Return the *top* most common (value, count) pairs."""
    return counter.most_common(top)


def render_count_table(
    counts: list[tuple[str, int]],
    field: str,
    total: int = 0,
) -> str:
    """Render a simple ASCII table of value counts."""
    if not counts:
        return f"No values found for field '{field}'."

    max_val_len = max(len(v) for v, _ in counts)
    max_val_len = max(max_val_len, len(field))
    header = f"{field:<{max_val_len}}  {'count':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for value, count in counts:
        pct = f"  ({100 * count / total:.1f}%)" if total else ""
        lines.append(f"{value:<{max_val_len}}  {count:>8}{pct}")
    if total:
        lines.append(sep)
        lines.append(f"{'TOTAL':<{max_val_len}}  {total:>8}")
    return "\n".join(lines)

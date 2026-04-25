"""Group log records into discrete field-value buckets for analysis."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple


def parse_bucket_field_expr(expr: str) -> Tuple[str, Optional[List[str]]]:
    """Parse 'field' or 'field:v1,v2,v3' into (field, buckets_or_None)."""
    if not expr or not expr.strip():
        raise ValueError("bucket expression must not be empty")
    parts = expr.strip().split(":", 1)
    field = parts[0].strip()
    if not field:
        raise ValueError("field name must not be empty")
    if len(parts) == 2 and parts[1].strip():
        buckets = [v.strip() for v in parts[1].split(",") if v.strip()]
        return field, buckets
    return field, None


def bucket_records(
    records: Iterable[dict],
    field: str,
    buckets: Optional[List[str]] = None,
) -> Dict[str, List[dict]]:
    """Group records by the value of *field*.

    If *buckets* is provided only those bucket keys are kept; records whose
    field value is not in the list are placed under the key ``"__other__"``.
    Records missing the field entirely go under ``"__missing__"``.
    """
    groups: Dict[str, List[dict]] = defaultdict(list)
    bucket_set = set(buckets) if buckets else None

    for rec in records:
        val = rec.get(field)
        if val is None:
            key = "__missing__"
        else:
            key = str(val)
            if bucket_set is not None and key not in bucket_set:
                key = "__other__"
        groups[key].append(rec)

    return dict(groups)


def render_bucket_summary(groups: Dict[str, List[dict]], field: str) -> str:
    """Return a human-readable summary table of bucket sizes."""
    lines = [f"Buckets for field '{field}':", "-" * 40]
    total = sum(len(v) for v in groups.values())
    for key in sorted(groups):
        count = len(groups[key])
        pct = 100.0 * count / total if total else 0.0
        lines.append(f"  {key:<25} {count:>6}  ({pct:5.1f}%)")
    lines.append("-" * 40)
    lines.append(f"  {'TOTAL':<25} {total:>6}")
    return "\n".join(lines)

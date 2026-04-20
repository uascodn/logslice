"""Pivot log records: group by a field and collect values of another field."""
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple


def pivot_records(
    records: List[Dict[str, Any]],
    row_field: str,
    col_field: str,
    val_field: Optional[str] = None,
    agg: str = "count",
) -> Dict[str, Dict[str, Any]]:
    """Return {row_value: {col_value: aggregated}} mapping."""
    buckets: Dict[str, Dict[str, List]] = defaultdict(lambda: defaultdict(list))
    for rec in records:
        row = str(rec.get(row_field, ""))
        col = str(rec.get(col_field, ""))
        val = rec.get(val_field) if val_field else None
        buckets[row][col].append(val)

    result: Dict[str, Dict[str, Any]] = {}
    for row, cols in buckets.items():
        result[row] = {}
        for col, vals in cols.items():
            result[row][col] = _aggregate(vals, agg)
    return result


def _aggregate(values: List, agg: str) -> Any:
    if agg == "count":
        return len(values)
    numeric = [v for v in values if isinstance(v, (int, float))]
    if agg == "sum":
        return sum(numeric)
    if agg == "avg":
        return sum(numeric) / len(numeric) if numeric else None
    if agg == "min":
        return min(numeric) if numeric else None
    if agg == "max":
        return max(numeric) if numeric else None
    raise ValueError(f"Unknown aggregation: {agg}")


def parse_pivot_expr(expr: str) -> Tuple[str, str, Optional[str], str]:
    """Parse 'row=<f>,col=<f>[,val=<f>][,agg=<agg>]' into tuple."""
    parts = dict(p.split("=", 1) for p in expr.split(",") if "=" in p)
    row = parts.get("row", "")
    col = parts.get("col", "")
    val = parts.get("val", None)
    agg = parts.get("agg", "count")
    if not row or not col:
        raise ValueError("pivot expr requires row=<field>,col=<field>")
    return row, col, val, agg


def render_pivot_table(pivot: Dict[str, Dict[str, Any]]) -> str:
    """Render pivot dict as a simple text table."""
    if not pivot:
        return "(empty)"
    all_cols = sorted({col for row in pivot.values() for col in row})
    col_w = [max(len(c), 6) for c in all_cols]
    row_w = max((len(r) for r in pivot), default=8)
    header = f"{'':>{row_w}}  " + "  ".join(c.ljust(w) for c, w in zip(all_cols, col_w))
    lines = [header, "-" * len(header)]
    for row_val in sorted(pivot):
        cells = [str(pivot[row_val].get(c, "")).ljust(w) for c, w in zip(all_cols, col_w)]
        lines.append(f"{row_val:>{row_w}}  " + "  ".join(cells))
    return "\n".join(lines)

"""Rollup: group records by a field and compute aggregate metrics."""

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional


def parse_rollup_expr(expr: str):
    """Parse a rollup expression like 'service:count,latency:sum'.

    Returns (group_by_field, [(metric_name, agg_func), ...])
    """
    if ":" not in expr:
        raise ValueError(f"Invalid rollup expression: {expr!r}")
    parts = expr.split(",")
    group_field, first_metric = parts[0].split(":", 1)
    metrics = [(group_field.strip(), first_metric.strip())]
    for part in parts[1:]:
        if ":" not in part:
            raise ValueError(f"Invalid metric spec: {part!r}")
        field, func = part.split(":", 1)
        metrics.append((field.strip(), func.strip()))
    return group_field.strip(), metrics[1:] if len(metrics) > 1 else [("count", "count")]


SUPPORTED_FUNCS = {"count", "sum", "avg", "min", "max"}


def rollup_records(
    records: Iterable[Dict[str, Any]],
    group_by: str,
    metrics: List[tuple],
) -> List[Dict[str, Any]]:
    """Group records by `group_by` field and apply aggregate metrics.

    metrics: list of (field, func) pairs, e.g. [("latency", "avg"), ("count", "count")]
    """
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        key = str(rec.get(group_by, "__missing__"))
        buckets[key].append(rec)

    results = []
    for group_val, group_recs in sorted(buckets.items()):
        row: Dict[str, Any] = {group_by: group_val, "_count": len(group_recs)}
        for field, func in metrics:
            func = func.lower()
            if func not in SUPPORTED_FUNCS:
                raise ValueError(f"Unsupported aggregation function: {func!r}")
            if func == "count":
                row[f"{field}_{func}"] = len(group_recs)
            else:
                values = []
                for r in group_recs:
                    try:
                        values.append(float(r[field]))
                    except (KeyError, TypeError, ValueError):
                        pass
                if not values:
                    row[f"{field}_{func}"] = None
                elif func == "sum":
                    row[f"{field}_{func}"] = sum(values)
                elif func == "avg":
                    row[f"{field}_{func}"] = sum(values) / len(values)
                elif func == "min":
                    row[f"{field}_{func}"] = min(values)
                elif func == "max":
                    row[f"{field}_{func}"] = max(values)
        results.append(row)
    return results


def render_rollup_table(results: List[Dict[str, Any]]) -> str:
    """Render rollup results as a plain-text table."""
    if not results:
        return "(no data)"
    headers = list(results[0].keys())
    col_widths = {h: len(h) for h in headers}
    rows = []
    for row in results:
        formatted = {}
        for h in headers:
            val = row.get(h)
            s = f"{val:.4g}" if isinstance(val, float) else str(val) if val is not None else ""
            formatted[h] = s
            col_widths[h] = max(col_widths[h], len(s))
        rows.append(formatted)
    sep = "+" + "+".join("-" * (col_widths[h] + 2) for h in headers) + "+"
    header_line = "|" + "|".join(f" {h:<{col_widths[h]}} " for h in headers) + "|"
    lines = [sep, header_line, sep]
    for row in rows:
        lines.append("|" + "|".join(f" {row[h]:<{col_widths[h]}} " for h in headers) + "|")
    lines.append(sep)
    return "\n".join(lines)

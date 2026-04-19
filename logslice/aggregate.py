"""Aggregation helpers: count, sum, avg, min, max over a field."""
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional


AGG_FUNCS = ("count", "sum", "avg", "min", "max")


class Aggregator:
    def __init__(self, group_by: Optional[str], agg_func: str, field: Optional[str] = None):
        if agg_func not in AGG_FUNCS:
            raise ValueError(f"Unknown aggregation function: {agg_func!r}")
        if agg_func != "count" and field is None:
            raise ValueError(f"Field required for aggregation function {agg_func!r}")
        self.group_by = group_by
        self.agg_func = agg_func
        self.field = field
        self._counts: Dict[Any, int] = defaultdict(int)
        self._values: Dict[Any, List[float]] = defaultdict(list)

    def feed(self, record: Dict[str, Any]) -> None:
        key = record.get(self.group_by) if self.group_by else "_all"
        self._counts[key] += 1
        if self.field and self.field in record:
            try:
                self._values[key].append(float(record[self.field]))
            except (TypeError, ValueError):
                pass

    def result(self) -> Dict[Any, Any]:
        out = {}
        for key in self._counts:
            if self.agg_func == "count":
                out[key] = self._counts[key]
            else:
                vals = self._values.get(key, [])
                if not vals:
                    out[key] = None
                elif self.agg_func == "sum":
                    out[key] = sum(vals)
                elif self.agg_func == "avg":
                    out[key] = sum(vals) / len(vals)
                elif self.agg_func == "min":
                    out[key] = min(vals)
                elif self.agg_func == "max":
                    out[key] = max(vals)
        return out


def parse_agg_expr(expr: str):
    """Parse expressions like 'count', 'sum:latency', 'avg:duration' optionally with 'by:field'.

    Full syntax: '<func>[:<field>][,by:<group_field>]'
    Example: 'avg:latency,by:service'
    """
    parts = [p.strip() for p in expr.split(",")]
    func_part = parts[0]
    group_by = None
    for p in parts[1:]:
        if p.startswith("by:"):
            group_by = p[3:]
    if ":" in func_part:
        func, field = func_part.split(":", 1)
    else:
        func, field = func_part, None
    return Aggregator(group_by=group_by, agg_func=func, field=field)

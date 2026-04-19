"""Render summary reports from Stats and Aggregator results."""
from typing import Any, Dict, Optional

from logslice.stats import Stats


def render_report(stats: Stats, agg_results: Optional[Dict[str, Any]] = None) -> str:
    lines = []
    lines.append("=== logslice report ===")
    lines.append(f"  total lines   : {stats.total}")
    lines.append(f"  matched lines : {stats.matched}")
    lines.append(f"  dropped lines : {stats.dropped}")

    for field, counter in stats._counters.items():
        top = stats.top_values(field, n=5)
        if not top:
            continue
        lines.append(f"  top {field}:")
        for value, count in top:
            lines.append(f"    {value!s:<30} {count}")

    if agg_results:
        lines.append("  aggregations:")
        for label, result in agg_results.items():
            lines.append(f"    {label}:")
            if isinstance(result, dict):
                for k, v in sorted(result.items(), key=lambda x: str(x[0])):
                    v_str = f"{v:.4g}" if isinstance(v, float) else str(v)
                    lines.append(f"      {k!s:<28} {v_str}")
            else:
                lines.append(f"      {result}")

    lines.append("=" * 23)
    return "\n".join(lines)

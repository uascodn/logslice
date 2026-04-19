"""Human-readable report rendering for Stats."""
from typing import IO, Optional
from logslice.stats import Stats


def render_report(
    stats: Stats,
    out: IO,
    top_fields: Optional[list] = None,
    top_n: int = 5,
) -> None:
    """Write a stats report to *out*.

    Args:
        stats: populated Stats instance.
        out: writable text stream.
        top_fields: field names to show top-value breakdown for.
        top_n: how many top values to show per field.
    """
    summary = stats.summary()
    out.write("=== logslice report ===\n")
    out.write(f"  total lines  : {summary['total_lines']}\n")
    out.write(f"  matched lines: {summary['matched_lines']}\n")
    out.write(f"  dropped lines: {summary['dropped_lines']}\n")

    fields_to_show = top_fields if top_fields is not None else summary["fields_seen"]
    if fields_to_show:
        out.write("\n--- field breakdown ---\n")
        for field in fields_to_show:
            top = stats.top_values(field, n=top_n)
            if not top:
                continue
            unique = stats.unique_values(field)
            out.write(f"  {field} ({unique} unique):\n")
            for value, count in top:
                bar = "#" * min(count, 20)
                out.write(f"    {value:<20} {count:>6}  {bar}\n")
    out.write("======================\n")

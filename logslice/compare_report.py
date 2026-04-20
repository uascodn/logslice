"""Render a human-readable comparison report."""
from __future__ import annotations

from typing import Iterable


def render_compare_report(diff_records: Iterable[dict]) -> str:
    lines: list[str] = []
    only_a = only_b = changed = 0

    for rec in diff_records:
        status = rec.get("status")
        key_str = ", ".join(f"{k}={v}" for k, v in rec["key"].items())
        if status == "only_in_a":
            only_a += 1
            lines.append(f"  [only_in_a] {key_str}")
        elif status == "only_in_b":
            only_b += 1
            lines.append(f"  [only_in_b] {key_str}")
        elif status == "changed":
            changed += 1
            lines.append(f"  [changed]   {key_str}")
            for field, vals in rec.get("diffs", {}).items():
                lines.append(f"    {field}: {vals['a']!r} -> {vals['b']!r}")

    header = [
        "=== logslice compare report ===",
        f"  only in A : {only_a}",
        f"  only in B : {only_b}",
        f"  changed   : {changed}",
        "",
    ]
    return "\n".join(header + lines)

"""CLI sub-command: resample — aggregate log records into time buckets."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.resample import parse_resample_expr, resample_records


def build_resample_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="logslice resample",
        description="Aggregate log records into fixed-size time buckets.",
    )
    if parent is not None:
        parser = parent.add_parser("resample", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument(
        "expr",
        help="Resample expression, e.g. '5m:count', '1h:avg:latency', '30s:sum:bytes'.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json).",
    )
    return parser


def _render_table(rows: List[dict]) -> str:
    if not rows:
        return "(no data)"
    lines = [f"{'bucket':<32} {'value':>12}  count"]
    lines.append("-" * 52)
    for row in rows:
        val = row["value"]
        val_str = f"{val:.4g}" if isinstance(val, float) else str(val)
        lines.append(f"{row['bucket']:<32} {val_str:>12}  {row['count']}")
    return "\n".join(lines)


def run_resample(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    try:
        bucket_seconds, agg_spec = parse_resample_expr(args.expr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    agg_parts = agg_spec.split(":", 1)
    agg = agg_parts[0]
    field = agg_parts[1] if len(agg_parts) > 1 else None

    src = sys.stdin if args.input == "-" else open(args.input)
    try:
        records = [r for line in src if (r := parse_line(line)) is not None]
    finally:
        if src is not sys.stdin:
            src.close()

    try:
        rows = resample_records(records, bucket_seconds, agg, field)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        for row in rows:
            print(json.dumps(row), file=out)
    else:
        print(_render_table(rows), file=out)


def main() -> None:
    parser = build_resample_parser()
    args = parser.parse_args()
    run_resample(args)


if __name__ == "__main__":
    main()

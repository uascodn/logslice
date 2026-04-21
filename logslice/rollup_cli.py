"""CLI entry point for the rollup sub-command."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.rollup import parse_rollup_expr, rollup_records, render_rollup_table


def build_rollup_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Group log records by a field and compute aggregate metrics."
    if parent is not None:
        p = parent.add_parser("rollup", description=description, help=description)
    else:
        p = argparse.ArgumentParser(prog="logslice rollup", description=description)
    p.add_argument("file", nargs="?", default="-", help="Input log file (default: stdin)")
    p.add_argument(
        "--by",
        required=True,
        metavar="FIELD",
        help="Field to group by (e.g. 'service')",
    )
    p.add_argument(
        "--metric",
        dest="metrics",
        action="append",
        default=[],
        metavar="FIELD:FUNC",
        help="Metric to compute, e.g. latency:avg. Repeatable.",
    )
    p.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return p


def run_rollup(args: argparse.Namespace, out=None) -> int:
    if out is None:
        out = sys.stdout

    metrics: List[tuple] = []
    for expr in args.metrics:
        if ":" not in expr:
            print(f"error: invalid metric expression {expr!r}", file=sys.stderr)
            return 1
        field, func = expr.split(":", 1)
        metrics.append((field.strip(), func.strip()))

    if not metrics:
        metrics = [("count", "count")]

    src = args.file
    try:
        fh = sys.stdin if src == "-" else open(src)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    records = []
    with fh:
        for line in fh:
            rec = parse_line(line)
            if rec is not None:
                records.append(rec)

    try:
        results = rollup_records(records, group_by=args.by, metrics=metrics)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output == "json":
        for row in results:
            print(json.dumps(row), file=out)
    else:
        print(render_rollup_table(results), file=out)

    return 0


def main() -> None:
    parser = build_rollup_parser()
    args = parser.parse_args()
    sys.exit(run_rollup(args))


if __name__ == "__main__":
    main()
